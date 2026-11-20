from typing import Optional
from pathlib import Path
import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

import carnet_observations
from modele_fructification import (
    CATALOGUE_ESPECES,
    simuler_pousse_point_gps,
    rechercher_zones_optimales_5km,
)

app = FastAPI(
    title="Simulateur Bioclimatique et Édaphique de Fructification",
    description="Prédiction de pousse de champignons sauvages comestibles (J à J+10)",
    version="2.0.0",
)

# Cache mémoire pour réponses sub-millisecondes (TTL 30 minutes)
_CACHE_API_SIMULER = {}
_CACHE_API_RADAR = {}

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
IMG_DIR = STATIC_DIR / "img"
IMG_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="img")


@app.get("/")
def afficher_interface():
    """Sert l'application web cartographique Leaflet.js."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/manifest.json")
def get_manifest():
    """Manifest PWA pour l'installation sur mobile (Android & iPhone)."""
    return FileResponse(str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json")


@app.get("/favicon.png")
def get_favicon():
    """Favicon de l'application."""
    return FileResponse(str(STATIC_DIR / "favicon.png"))


@app.get("/api/especes")
def lister_catalogue_especes():
    """Renvoie la totalité du catalogue maître des 80 espèces comestibles."""
    return {"total": len(CATALOGUE_ESPECES), "especes": CATALOGUE_ESPECES}


@app.get("/api/simuler")
def api_simuler_point(
    lat: float = Query(..., description="Latitude du point GPS", ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude du point GPS", ge=-180.0, le=180.0),
):
    """
    Exécute la simulation bioclimatique et édaphique complète sur (lat, lon)
    et renvoie l'environnement, la météo (J-20 à J+10) et les scores de J à J+10.
    Réponse quasi-instantanée grâce au cache mémoire spatial.
    """
    cache_key = (round(lat, 4), round(lon, 4))
    maintenant = time.time()
    if cache_key in _CACHE_API_SIMULER:
        res, exp = _CACHE_API_SIMULER[cache_key]
        if maintenant < exp:
            return res

    try:
        data = simuler_pousse_point_gps(round(lat, 5), round(lon, 5))
        _CACHE_API_SIMULER[cache_key] = (data, maintenant + 1800)
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/zones-espece")
def api_zones_espece_5km(
    lat: float = Query(..., description="Latitude du centre", ge=-90.0, le=90.0),
    lon: float = Query(..., description="Longitude du centre", ge=-180.0, le=180.0),
    espece_id: Optional[str] = Query(None, description="Identifiant de l'espèce"),
    nom_espece: Optional[str] = Query(None, description="Nom vernaculaire de l'espèce"),
    rayon_km: float = Query(5.0, description="Rayon de recherche en km", ge=1.0, le=10.0),
    decalage_jour: Optional[int] = Query(None, description="Échéance en jours (0=J, ..., 10=J+10)"),
    jour_idx: Optional[int] = Query(None, description="Index du jour"),
):
    """
    Scanne un rayon de 5 km autour de (lat, lon) pour une espèce donnée et renvoie
    les meilleures zones de récolte (forêts IGN, lisières, prairies, versants).
    Accepte indifféremment espece_id ou nom_espece, ainsi que decalage_jour ou jour_idx.
    """
    target_espece = espece_id or nom_espece
    if not target_espece:
        raise HTTPException(status_code=422, detail="Veuillez spécifier espece_id ou nom_espece.")
    target_jour = decalage_jour if decalage_jour is not None else (jour_idx if jour_idx is not None else 0)

    cache_key = (round(lat, 3), round(lon, 3), str(target_espece).lower(), round(rayon_km, 1), target_jour)
    maintenant = time.time()
    if cache_key in _CACHE_API_RADAR:
        res, exp = _CACHE_API_RADAR[cache_key]
        if maintenant < exp:
            return res

    try:
        data = rechercher_zones_optimales_5km(
            round(lat, 5),
            round(lon, 5),
            espece_id=target_espece,
            rayon_km=rayon_km,
            decalage_jour=target_jour,
        )
        _CACHE_API_RADAR[cache_key] = (data, maintenant + 1800)
        return data
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ==============================================================================
# AUTOROUTE D'OBSERVATIONS & AUTO-CALIBRATION DU MODÈLE (ESPACE CONCEPTEUR)
# ==============================================================================

@app.get("/api/concepteur/observations")
def api_lister_observations():
    """Renvoie la totalité des observations terrain et le tableau de bord concepteur."""
    return {
        "observations": carnet_observations.lister_observations(),
        "tableau_de_bord": carnet_observations.obtenir_tableau_de_bord_concepteur(),
    }


@app.post("/api/concepteur/observations")
async def api_ajouter_observation(request: Request):
    """
    Enregistre une cueillette réelle du concepteur et recalibre immédiatement
    le modèle bioclimatique pour les espèces concernées.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Corps JSON invalide.")

    lat = data.get("lat")
    lon = data.get("lon")
    espece_id = data.get("espece_id")
    nom_espece = data.get("nom_espece") or espece_id
    if lat is None or lon is None or not espece_id:
        raise HTTPException(status_code=422, detail="Latitude, longitude et espece_id sont requis.")

    res = carnet_observations.ajouter_observation(
        lat=float(lat),
        lon=float(lon),
        espece_id=str(espece_id),
        nom_espece=str(nom_espece),
        date_obs=data.get("date"),
        abondance=data.get("abondance", "moderee"),
        quantite_kg=data.get("quantite_kg"),
        stade=data.get("stade", "adulte"),
        score_predit=data.get("score_predit"),
        commentaire=data.get("commentaire", ""),
        biotope_observe=data.get("biotope_observe", ""),
    )

    # Réinitialisation des caches prédictifs en mémoire pour réactivité instantanée
    _CACHE_API_SIMULER.clear()
    _CACHE_API_RADAR.clear()

    return res


@app.delete("/api/concepteur/observations/{obs_id}")
def api_supprimer_observation(obs_id: str):
    """Supprime une observation erronée et recalibre le modèle."""
    succes = carnet_observations.supprimer_observation(obs_id)
    if not succes:
        raise HTTPException(status_code=404, detail="Observation introuvable.")
    _CACHE_API_SIMULER.clear()
    _CACHE_API_RADAR.clear()
    return {"statut": "succes", "message": "Observation supprimée et modèle recalibré."}


@app.get("/api/concepteur/dashboard")
def api_dashboard_concepteur():
    """Statistiques, matrice de précision et coefficients actifs de calibration."""
    return carnet_observations.obtenir_tableau_de_bord_concepteur()


@app.get("/api/concepteur/export")
def api_export_observations(format: str = Query("json", regex="^(json|csv)$")):
    """Exporte les données terrain pour SIG, tableur Excel ou analyse."""
    if format == "csv":
        csv_data = carnet_observations.exporter_observations_csv()
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=observations_cueillettes.csv"},
        )
    return carnet_observations.lister_observations()

