"""
Module de gestion du carnet d'observations terrain du concepteur et calibrage automatique du modèle de prédiction.

Permet au concepteur d'enregistrer en 1 clic ses cueillettes et observations réelles,
de comparer la réalité du terrain avec les prédictions du modèle,
et d'adapter dynamiquement les coefficients bioclimatiques (auto-calibration continue).
"""

from datetime import datetime
import json
import math
import os
import uuid
from typing import Any, Dict, List, Optional

FICHIER_OBSERVATIONS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "observations_concepteur.json"
)

# Barème de conversion de l'abondance observée en score réel équivalent (0-100)
BAREME_ABONDANCE = {
    "nulle": {"label": "🚫 Bredouille (0 spécimen)", "score_reel": 0.0, "poids": 1.0},
    "rare": {"label": "🍄 Rare (1 à 3 spécimens)", "score_reel": 40.0, "poids": 1.0},
    "moderee": {"label": "🧺 Récolte moyenne (4 à 10 spécimens)", "score_reel": 75.0, "poids": 1.2},
    "abondante": {"label": "🌟 Plein panier (> 10 spécimens / > 1 kg)", "score_reel": 95.0, "poids": 1.5},
    "exceptionnelle": {"label": "🔥 Explosion / Fructification massive", "score_reel": 100.0, "poids": 1.8},
}

# Cache en mémoire des calibrations actives
_CALIBRATIONS_CACHE: Dict[str, Dict[str, Any]] = {}
_INITIALISE = False

MAPPING_ALIAS = {
    "hydnum_repandum": "pied_de_mouton",
    "hydnum_rufescens": "pied_de_mouton_roussissant",
    "boletus_edulis": "cepe_bordeaux",
    "boletus_pinophilus": "cepe_des_pins",
    "boletus_aereus": "cepe_tete_de_negre",
    "boletus_reticulatus": "cepe_ete",
    "cantharellus_cibarius": "girolle",
    "craterellus_cornucopioides": "trompette_de_la_mort",
    "amanita_caesarea": "oronge",
    "macrolepiota_procera": "coulemelle",
    "lactarius_deliciosus": "lactaire_delicieux",
    "lactarius_sanguifluus": "lactaire_sanguin",
    "morchella_esculenta": "morille_commune",
    "morchella_elata": "morille_conique",
}


def normaliser_espece_id(identifiant_ou_nom: str) -> str:
    """Normalise un identifiant ou nom scientifique vers l'ID canonique du catalogue."""
    s = str(identifiant_ou_nom).strip().lower().replace("-", "_").replace(" ", "_")
    return MAPPING_ALIAS.get(s, s)


def _charger_donnees() -> List[Dict[str, Any]]:
    if not os.path.exists(FICHIER_OBSERVATIONS):
        return []
    try:
        with open(FICHIER_OBSERVATIONS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _sauvegarder_donnees(observations: List[Dict[str, Any]]) -> bool:
    os.makedirs(os.path.dirname(FICHIER_OBSERVATIONS), exist_ok=True)
    try:
        with open(FICHIER_OBSERVATIONS, "w", encoding="utf-8") as f:
            json.dump(observations, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def recalculer_calibrations() -> Dict[str, Any]:
    """
    Analyse l'historique de toutes les observations réelles du concepteur
    et calcule pour chaque espèce un coefficient de calibration empirique
    ainsi que les métriques d'évaluation du modèle.
    """
    global _CALIBRATIONS_CACHE, _INITIALISE
    observations = _charger_donnees()
    calibrations: Dict[str, Dict[str, Any]] = {}

    # Regrouper par espèce
    par_espece: Dict[str, List[Dict[str, Any]]] = {}
    for obs in observations:
        esp = normaliser_espece_id(obs.get("espece_id", "inconnu"))
        par_espece.setdefault(esp, []).append(obs)

    total_predits_corrects = 0
    total_evaluables = 0

    for esp, liste_obs in par_espece.items():
        delta_pondere_sum = 0.0
        poids_total = 0.0
        succes_reels = 0
        fausses_alertes = 0
        trouvailles_inattendues = 0

        for obs in liste_obs:
            abondance = obs.get("abondance", "moderee")
            bareme = BAREME_ABONDANCE.get(abondance, BAREME_ABONDANCE["moderee"])
            score_reel = bareme["score_reel"]
            poids = bareme["poids"]

            # Score prédit par le modèle à ce moment (ou estimé par défaut à 50 si non fourni)
            score_predit = obs.get("score_predit")
            if score_predit is None:
                score_predit = 50.0
            else:
                score_predit = float(score_predit)

            total_evaluables += 1
            # Concordance binaire (seuil 50 %)
            est_predit_positif = score_predit >= 50.0
            est_reel_positif = score_reel >= 50.0

            if est_predit_positif == est_reel_positif:
                total_predits_corrects += 1

            if est_predit_positif and est_reel_positif:
                succes_reels += 1
            elif est_predit_positif and not est_reel_positif:
                fausses_alertes += 1
            elif not est_predit_positif and est_reel_positif:
                trouvailles_inattendues += 1

            # Écart (Positif = le modèle sous-estimait, Négatif = le modèle surestimait)
            delta = score_reel - score_predit
            delta_pondere_sum += delta * poids
            poids_total += poids

        # Facteur empirique lissé :
        # - Évite les oscillations brutales sur un échantillon faible
        # - Plafonne l'effet multiplicateur entre 0.70 (-30 %) et 1.35 (+35 %)
        if poids_total > 0:
            biais_moyen = delta_pondere_sum / poids_total
            # Amortissement bayésien avec a priori neutre (confiance croissante avec N)
            confiance_n = min(1.0, len(liste_obs) / 4.0)
            ajustement = (biais_moyen / 100.0) * 0.40 * confiance_n
            facteur = round(max(0.70, min(1.35, 1.0 + ajustement)), 3)
        else:
            facteur = 1.0

        nom_esp = liste_obs[-1].get("nom_espece") or esp
        calibrations[esp] = {
            "espece_id": esp,
            "nom_espece": nom_esp,
            "nb_observations": len(liste_obs),
            "facteur_calibration": facteur,
            "gain_pourcentage": round((facteur - 1.0) * 100, 1),
            "succes_reels": succes_reels,
            "fausses_alertes": fausses_alertes,
            "trouvailles_inattendues": trouvailles_inattendues,
            "derniere_observation": liste_obs[-1].get("date"),
        }

    _CALIBRATIONS_CACHE = calibrations
    _INITIALISE = True

    taux_precision = (
        round((total_predits_corrects / total_evaluables) * 100, 1)
        if total_evaluables > 0
        else 100.0
    )

    return {
        "calibrations": calibrations,
        "total_observations": len(observations),
        "total_evaluables": total_evaluables,
        "taux_precision_pct": taux_precision,
    }


def initialiser_si_besoin():
    global _INITIALISE
    if not _INITIALISE:
        recalculer_calibrations()


def obtenir_facteur_calibration(espece_id: str) -> float:
    """
    Renvoie le facteur correcteur multiplicatif (ex: 1.15) pour l'espèce donnée,
    calculé à partir des retours réels du concepteur.
    """
    initialiser_si_besoin()
    cle = normaliser_espece_id(espece_id)
    calib = _CALIBRATIONS_CACHE.get(cle) or _CALIBRATIONS_CACHE.get(espece_id)
    if calib:
        return calib.get("facteur_calibration", 1.0)
    return 1.0


def ajouter_observation(
    lat: float,
    lon: float,
    espece_id: str,
    nom_espece: str,
    date_obs: Optional[str] = None,
    abondance: str = "moderee",
    quantite_kg: Optional[float] = None,
    stade: str = "adulte",
    score_predit: Optional[float] = None,
    commentaire: str = "",
    biotope_observe: str = "",
) -> Dict[str, Any]:
    """
    Enregistre une cueillette réelle du concepteur et recalibre instantanément le modèle.
    """
    observations = _charger_donnees()
    date_str = date_obs or datetime.now().strftime("%Y-%m-%d")

    nouvelle_obs = {
        "id": f"obs_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:6]}",
        "date": date_str,
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "espece_id": str(espece_id).strip(),
        "nom_espece": str(nom_espece).strip(),
        "abondance": abondance if abondance in BAREME_ABONDANCE else "moderee",
        "quantite_kg": float(quantite_kg) if quantite_kg is not None else None,
        "stade": stade,  # "primordium", "adulte", "mature_avance"
        "score_predit": round(float(score_predit), 1) if score_predit is not None else None,
        "commentaire": commentaire.strip(),
        "biotope_observe": biotope_observe.strip(),
        "horodatage_iso": datetime.now().isoformat(),
        "auteur": "Concepteur",
    }

    observations.insert(0, nouvelle_obs)  # Plus récent en premier
    _sauvegarder_donnees(observations)

    # Recalibrer immédiatement le modèle avec ce nouveau retour d'expérience
    stats_calib = recalculer_calibrations()
    nouvel_impact = _CALIBRATIONS_CACHE.get(espece_id, {})

    return {
        "statut": "succes",
        "message": f"Observation enregistrée avec succès pour {nom_espece} !",
        "observation": nouvelle_obs,
        "impact_calibration": nouvel_impact,
        "stats_globales": stats_calib,
    }


def lister_observations() -> List[Dict[str, Any]]:
    """Renvoie la liste chronologique de toutes les observations terrain."""
    return _charger_donnees()


def supprimer_observation(obs_id: str) -> bool:
    """Supprime une observation et recalibre le modèle."""
    observations = _charger_donnees()
    nouvelle_liste = [o for o in observations if o.get("id") != obs_id]
    if len(nouvelle_liste) != len(observations):
        _sauvegarder_donnees(nouvelle_liste)
        recalculer_calibrations()
        return True
    return False


def obtenir_tableau_de_bord_concepteur() -> Dict[str, Any]:
    """
    Synthétise le tableau de bord complet pour le concepteur :
    - Observations terrain passées
    - Facteurs de calibration actifs
    - Score de fidélité / précision du modèle
    - Espèces les plus fructifères
    """
    initialiser_si_besoin()
    observations = _charger_donnees()
    recalculer_calibrations()

    # Statistiques d'abondance
    compte_abondance = {}
    for o in observations:
        ab = o.get("abondance", "autre")
        compte_abondance[ab] = compte_abondance.get(ab, 0) + 1

    total = len(observations)
    taux_succes = 0.0
    if total > 0:
        succes = sum(
            1 for o in observations if o.get("abondance") in ("moderee", "abondante", "exceptionnelle")
        )
        taux_succes = round((succes / total) * 100, 1)

    return {
        "total_observations": total,
        "taux_recolte_positive_pct": taux_succes,
        "repartition_abondance": compte_abondance,
        "calibrations_actives": list(_CALIBRATIONS_CACHE.values()),
        "nb_especes_calibrees": len(_CALIBRATIONS_CACHE),
        "dernieres_observations": observations[:20],
    }


def exporter_observations_csv() -> str:
    """Génère un export au format CSV des observations pour analyse tableur / SIG."""
    observations = _charger_donnees()
    lignes = [
        "id;date;lat;lon;espece_id;nom_espece;abondance;quantite_kg;stade;score_predit;biotope;commentaire"
    ]
    for o in observations:
        lignes.append(
            f"{o.get('id','')};{o.get('date','')};{o.get('lat','')};{o.get('lon','')};"
            f"{o.get('espece_id','')};\"{o.get('nom_espece','')}\";{o.get('abondance','')};"
            f"{o.get('quantite_kg','')};{o.get('stade','')};{o.get('score_predit','')};"
            f"\"{o.get('biotope_observe','')}\";\"{o.get('commentaire','')}\""
        )
    return "\n".join(lignes)
