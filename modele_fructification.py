import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from meteo import recuperer_donnees_meteo
from environnement import (
    recuperer_profil_environnemental,
    recuperer_donnees_sol,
    calculer_distance_et_cap,
    construire_mnt_rayon,
    calculer_topographie_sur_mnt,
    recuperer_polygones_foret_rayon,
    qualifier_point_dans_parcelles,
    estimer_sol_local_zone,
    _trouver_point_interieur_polygone,
    _simplifier_anneau_leaflet,
    _point_dans_polygone,
)


# Catalogue élargi des espèces de champignons sauvages comestibles (42 espèces)
CATALOGUE_ESPECES = [
    # --- CÈPES & BOLETS ---
    {
        "id": "cepe_bordeaux",
        "nom": "Cèpe de Bordeaux",
        "nom_scientifique": "Boletus edulis",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (8.5, 18.0),
        "temp_sol_limites": (3.5, 23.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "épicéa", "sapin", "pin", "feuillus", "conifères"],
        "altitude_max": 2200,
    },
    {
        "id": "cepe_ete",
        "nom": "Cèpe d'été (Réticulé)",
        "nom_scientifique": "Boletus reticulatus",
        "mois_actifs": [5, 6, 7, 8, 9, 10],
        "mois_optimaux": [6, 7, 8, 9],
        "ph_optimal": (5.0, 6.8),
        "temp_sol_optimale": (14.0, 22.0),
        "temp_sol_limites": (10.0, 26.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "charme", "feuillus"],
        "altitude_max": 1600,
    },
    {
        "id": "cepe_bronze",
        "nom": "Cèpe bronzé (Tête de nègre)",
        "nom_scientifique": "Boletus aereus",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (5.0, 6.8),
        "temp_sol_optimale": (14.0, 22.0),
        "temp_sol_limites": (10.0, 26.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (8, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "châtaignier", "hêtre", "feuillus"],
        "altitude_max": 1200,
    },
    {
        "id": "cepe_pins",
        "nom": "Cèpe des pins",
        "nom_scientifique": "Boletus pinophilus",
        "mois_actifs": [5, 6, 7, 8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.0, 6.0),
        "temp_sol_optimale": (9.0, 17.0),
        "temp_sol_limites": (5.0, 22.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "sapin", "épicéa", "conifères"],
        "altitude_max": 2000,
    },
    {
        "id": "bolet_bai",
        "nom": "Bolet bai",
        "nom_scientifique": "Imleria badia",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.2, 6.2),
        "temp_sol_optimale": (8.0, 17.0),
        "temp_sol_limites": (4.0, 21.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "épicéa", "sapin", "conifères", "chêne", "hêtre", "châtaignier", "feuillus"],
        "altitude_max": 2000,
    },
    {
        "id": "bolet_pied_rouge",
        "nom": "Bolet à pied rouge",
        "nom_scientifique": "Neoboletus erythropus",
        "mois_actifs": [5, 6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.2, 6.2),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 23.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "chêne", "châtaignier", "épicéa", "sapin", "feuillus", "conifères"],
        "altitude_max": 2200,
    },
    {
        "id": "bolet_rude",
        "nom": "Bolet rude (Bouleau)",
        "nom_scientifique": "Leccinum scabrum",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (7.5, 17.0),
        "temp_sol_limites": (3.0, 22.0),
        "pluie_20j_optimale_mm": (45.0, 120.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ["bouleau"],
        "altitude_max": 1800,
    },
    {
        "id": "bolet_orange",
        "nom": "Bolet orangé des chênes",
        "nom_scientifique": "Leccinum aurantiacum",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.8, 6.8),
        "temp_sol_optimale": (8.0, 18.0),
        "temp_sol_limites": (3.5, 22.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "peuplier", "tremble", "hêtre", "feuillus"],
        "altitude_max": 1600,
    },
    {
        "id": "nonnette_voilee",
        "nom": "Nonnette voilée (Bolet jaune)",
        "nom_scientifique": "Suillus luteus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.2, 6.2),
        "temp_sol_optimale": (8.0, 16.0),
        "temp_sol_limites": (4.0, 20.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "conifères"],
        "altitude_max": 2000,
    },
    {
        "id": "bolet_mou",
        "nom": "Bolet mou (Bolet des bouviers)",
        "nom_scientifique": "Suillus bovinus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.0, 5.8),
        "temp_sol_optimale": (7.0, 15.0),
        "temp_sol_limites": (3.0, 19.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "conifères"],
        "altitude_max": 1800,
    },

    # --- CHANTERELLES, TROMPETTES & HYDNES ---
    {
        "id": "girolle",
        "nom": "Girolle (Chanterelle)",
        "nom_scientifique": "Cantharellus cibarius",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [6, 7, 9, 10],
        "ph_optimal": (4.5, 6.2),
        "temp_sol_optimale": (9.5, 19.0),
        "temp_sol_limites": (5.0, 24.0),
        "pluie_20j_optimale_mm": (45.0, 120.0),
        "delai_maturation_jours": (10, 18),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "bouleau", "épicéa", "pin", "feuillus", "conifères"],
        "altitude_max": 2000,
    },
    {
        "id": "chanterelle_tube",
        "nom": "Chanterelle en tube (Grise)",
        "nom_scientifique": "Craterellus tubaeformis",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11, 12],
        "ph_optimal": (4.0, 6.0),
        "temp_sol_optimale": (5.0, 13.0),
        "temp_sol_limites": (1.0, 17.0),
        "pluie_20j_optimale_mm": (50.0, 140.0),
        "delai_maturation_jours": (7, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ["épicéa", "sapin", "pin", "conifères", "hêtre", "chêne", "châtaignier", "feuillus"],
        "altitude_max": 2000,
    },
    {
        "id": "chanterelle_jaunissante",
        "nom": "Chanterelle jaunissante",
        "nom_scientifique": "Craterellus lutescens",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (5.0, 7.2),
        "temp_sol_optimale": (6.0, 14.0),
        "temp_sol_limites": (2.0, 18.0),
        "pluie_20j_optimale_mm": (45.0, 130.0),
        "delai_maturation_jours": (7, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "épicéa", "sapin", "conifères", "hêtre"],
        "altitude_max": 2000,
    },
    {
        "id": "trompette_mort",
        "nom": "Trompette de la mort",
        "nom_scientifique": "Craterellus cornucopioides",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (5.0, 7.2),
        "temp_sol_optimale": (7.0, 14.5),
        "temp_sol_limites": (3.0, 18.5),
        "pluie_20j_optimale_mm": (60.0, 145.0),
        "delai_maturation_jours": (7, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "chêne", "charme", "châtaignier", "feuillus"],
        "altitude_max": 1600,
    },
    {
        "id": "pied_de_mouton",
        "nom": "Pied-de-mouton",
        "nom_scientifique": "Hydnum repandum",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (4.5, 7.8),
        "temp_sol_optimale": (5.5, 14.5),
        "temp_sol_limites": (1.5, 18.5),
        "pluie_20j_optimale_mm": (38.0, 125.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "chêne", "châtaignier", "épicéa", "sapin", "pin", "feuillus", "conifères"],
        "altitude_max": 1800,
    },
    {
        "id": "pied_de_mouton_roussissant",
        "nom": "Pied-de-mouton roussissant",
        "nom_scientifique": "Hydnum rufescens",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (5.0, 13.0),
        "temp_sol_limites": (1.5, 17.0),
        "pluie_20j_optimale_mm": (45.0, 125.0),
        "delai_maturation_jours": (8, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ["épicéa", "sapin", "pin", "hêtre", "chêne", "conifères", "feuillus"],
        "altitude_max": 2000,
    },

    # --- AMANITES COMESTIBLES ---
    {
        "id": "amanite_rougissante",
        "nom": "Amanite rougissante (Golmotte)",
        "nom_scientifique": "Amanita rubescens",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.2, 6.5),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 23.0),
        "pluie_20j_optimale_mm": (30.0, 105.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "pin", "épicéa", "sapin", "feuillus", "conifères"],
        "altitude_max": 2000,
    },
    {
        "id": "amanite_cesars",
        "nom": "Amanite des Césars (Oronge)",
        "nom_scientifique": "Amanita caesarea",
        "mois_actifs": [7, 8, 9, 10],
        "mois_optimaux": [8, 9],
        "ph_optimal": (5.0, 6.8),
        "temp_sol_optimale": (16.0, 24.0),
        "temp_sol_limites": (12.0, 28.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "châtaignier", "feuillus"],
        "altitude_max": 1000,
    },
    {
        "id": "amanite_vaginee",
        "nom": "Amanite vaginée (Grisette)",
        "nom_scientifique": "Amanita vaginata",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (8.5, 18.0),
        "temp_sol_limites": (4.0, 23.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "bouleau", "châtaignier", "feuillus", "conifères"],
        "altitude_max": 2000,
    },

    # --- LACCAIRES, POLYPORES & FISTULINES ---
    {
        "id": "laccaire_amethyste",
        "nom": "Laccaire améthyste",
        "nom_scientifique": "Laccaria amethystina",
        "mois_actifs": [8, 9, 10, 11, 12],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (6.0, 15.0),
        "temp_sol_limites": (2.0, 20.0),
        "pluie_20j_optimale_mm": (40.0, 125.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "chêne", "châtaignier", "charme", "feuillus", "conifères"],
        "altitude_max": 1800,
    },
    {
        "id": "laccaire_laque",
        "nom": "Laccaire laqué",
        "nom_scientifique": "Laccaria laccata",
        "mois_actifs": [6, 7, 8, 9, 10, 11, 12],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.2, 7.0),
        "temp_sol_optimale": (6.0, 16.0),
        "temp_sol_limites": (2.0, 21.0),
        "pluie_20j_optimale_mm": (35.0, 120.0),
        "delai_maturation_jours": (4, 10),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "hêtre", "bouleau", "pin", "épicéa", "feuillus", "conifères"],
        "altitude_max": 2200,
    },
    {
        "id": "fistuline_hepatique",
        "nom": "Fistuline hépatique (Langue de bœuf)",
        "nom_scientifique": "Fistulina hepatica",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 22.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "châtaignier", "feuillus"],
        "altitude_max": 1400,
    },
    {
        "id": "poule_des_bois",
        "nom": "Poule des bois (Maitake)",
        "nom_scientifique": "Grifola frondosa",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.8, 6.5),
        "temp_sol_optimale": (8.0, 18.0),
        "temp_sol_limites": (3.5, 22.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "châtaignier", "hêtre", "charme", "feuillus"],
        "altitude_max": 1300,
    },
    {
        "id": "polypore_soufre",
        "nom": "Polypore soufré",
        "nom_scientifique": "Laetiporus sulphureus",
        "mois_actifs": [5, 6, 7, 8, 9, 10],
        "mois_optimaux": [5, 6, 9],
        "ph_optimal": (5.0, 7.0),
        "temp_sol_optimale": (12.0, 21.0),
        "temp_sol_limites": (8.0, 25.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "robinier", "saule", "peuplier", "châtaignier", "feuillus"],
        "altitude_max": 1500,
    },
    {
        "id": "sparassis_crepu",
        "nom": "Sparassis crépu (Morille des pins)",
        "nom_scientifique": "Sparassis crispa",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.2, 6.2),
        "temp_sol_optimale": (7.0, 15.0),
        "temp_sol_limites": (3.0, 19.0),
        "pluie_20j_optimale_mm": (45.0, 115.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "sapin", "épicéa", "douglas", "conifères"],
        "altitude_max": 1800,
    },

    # --- LACTAIRES & RUSSULES ---
    {
        "id": "lactaire_delicieux",
        "nom": "Lactaire délicieux (Catalan)",
        "nom_scientifique": "Lactarius deliciosus",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (8.0, 16.0),
        "temp_sol_limites": (3.0, 20.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "conifères"],
        "altitude_max": 1800,
    },
    {
        "id": "lactaire_sanguin",
        "nom": "Lactaire sanguin",
        "nom_scientifique": "Lactarius sanguifluus",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (6.2, 8.0),
        "temp_sol_optimale": (9.0, 17.0),
        "temp_sol_limites": (4.0, 21.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "conifères"],
        "altitude_max": 1600,
    },
    {
        "id": "russule_charbonniere",
        "nom": "Russule charbonnière",
        "nom_scientifique": "Russula cyanoxantha",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 23.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ["hêtre", "chêne", "châtaignier", "charme", "feuillus"],
        "altitude_max": 1800,
    },
    {
        "id": "russule_verdoyante",
        "nom": "Russule verdoyante (Palomet)",
        "nom_scientifique": "Russula virescens",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [7, 8, 9],
        "ph_optimal": (4.8, 6.5),
        "temp_sol_optimale": (13.0, 21.0),
        "temp_sol_limites": (9.0, 25.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "feuillus"],
        "altitude_max": 1400,
    },
    {
        "id": "russule_doree",
        "nom": "Russule dorée",
        "nom_scientifique": "Russula aurea",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [7, 8, 9],
        "ph_optimal": (5.0, 7.2),
        "temp_sol_optimale": (12.0, 20.0),
        "temp_sol_limites": (8.0, 24.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "feuillus", "épicéa"],
        "altitude_max": 1600,
    },

    # --- TRICHOLOMES, CLITOCYBES, PIEDS BLEUS & MEUNIERS ---
    {
        "id": "pied_bleu",
        "nom": "Pied bleu",
        "nom_scientifique": "Lepista nuda",
        "mois_actifs": [10, 11, 12, 1],
        "mois_optimaux": [10, 11, 12],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (4.0, 12.0),
        "temp_sol_limites": (1.0, 16.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "feuillus", "épicéa", "pin", "conifères"],
        "altitude_max": 1600,
    },
    {
        "id": "tricholome_terreux",
        "nom": "Tricholome terreux (Petit gris)",
        "nom_scientifique": "Tricholoma terreum",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11, 12],
        "ph_optimal": (6.0, 7.8),
        "temp_sol_optimale": (4.0, 13.0),
        "temp_sol_limites": (1.0, 17.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ["pin", "épicéa", "sapin", "conifères"],
        "altitude_max": 1800,
    },
    {
        "id": "mousseron_st_georges",
        "nom": "Mousseron de la Saint-Georges",
        "nom_scientifique": "Calocybe gambosa",
        "mois_actifs": [4, 5, 6],
        "mois_optimaux": [4, 5],
        "ph_optimal": (6.2, 7.8),
        "temp_sol_optimale": (9.0, 16.0),
        "temp_sol_limites": (5.0, 20.0),
        "pluie_20j_optimale_mm": (35.0, 90.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "hausse",
        "essences_hotes": ["prairie", "lisière", "frêne", "noisetier", "aubépine"],
        "altitude_max": 1600,
    },
    {
        "id": "tete_de_moine",
        "nom": "Tête de moine (Clitocybe géotrope)",
        "nom_scientifique": "Infundibulicybe geotropa",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (6.3, 8.0),
        "temp_sol_optimale": (5.0, 14.0),
        "temp_sol_limites": (1.5, 18.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ["prairie", "lisière", "hêtre", "chêne", "frêne", "sapin"],
        "altitude_max": 1700,
    },
    {
        "id": "meunier",
        "nom": "Meunier (Clitopile petite prune)",
        "nom_scientifique": "Clitopilus prunulus",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (7.5, 17.0),
        "temp_sol_limites": (3.0, 22.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "épicéa", "feuillus", "conifères"],
        "altitude_max": 1800,
    },

    # --- PLEUROTES, LÉPIOTES, AGARICS, COPRINS & MARASMES ---
    {
        "id": "pleurote_huitre",
        "nom": "Pleurote en huître",
        "nom_scientifique": "Pleurotus ostreatus",
        "mois_actifs": [10, 11, 12, 1, 2],
        "mois_optimaux": [11, 12, 1],
        "ph_optimal": (5.2, 7.5),
        "temp_sol_optimale": (2.5, 10.0),
        "temp_sol_limites": (0.0, 14.0),
        "pluie_20j_optimale_mm": (30.0, 95.0),
        "delai_maturation_jours": (4, 10),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "peuplier", "saule", "frêne", "charme", "noisetier"],
        "altitude_max": 1500,
    },
    {
        "id": "pholiote_peuplier",
        "nom": "Pholiote du peuplier (Pivoulade)",
        "nom_scientifique": "Cyclocybe cylindracea",
        "mois_actifs": [3, 4, 5, 9, 10, 11],
        "mois_optimaux": [4, 5, 9, 10, 11],
        "ph_optimal": (5.5, 7.5),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 22.0),
        "pluie_20j_optimale_mm": (30.0, 90.0),
        "delai_maturation_jours": (4, 10),
        "choc_thermique": "modere",
        "essences_hotes": ["peuplier", "saule", "orme", "frêne"],
        "altitude_max": 1200,
    },
    {
        "id": "coulemelle",
        "nom": "Coulemelle (Lépiote élevée)",
        "nom_scientifique": "Macrolepiota procera",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.8, 7.2),
        "temp_sol_optimale": (7.0, 17.5),
        "temp_sol_limites": (2.5, 22.0),
        "pluie_20j_optimale_mm": (30.0, 90.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "modere",
        "essences_hotes": ["chêne", "hêtre", "châtaignier", "feuillus", "pin", "conifères", "prairie"],
        "altitude_max": 1600,
    },
    {
        "id": "agaric_bois",
        "nom": "Agaric des bois (Rosé des bois)",
        "nom_scientifique": "Agaricus sylvicola",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.0, 7.2),
        "temp_sol_optimale": (7.0, 17.0),
        "temp_sol_limites": (2.5, 21.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (5, 10),
        "choc_thermique": "baisse",
        "essences_hotes": ["hêtre", "chêne", "châtaignier", "épicéa", "sapin", "feuillus", "conifères"],
        "altitude_max": 1700,
    },
    {
        "id": "rose_des_pres",
        "nom": "Rosé des prés",
        "nom_scientifique": "Agaricus campestris",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.8, 7.5),
        "temp_sol_optimale": (7.5, 18.0),
        "temp_sol_limites": (3.0, 22.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (4, 9),
        "choc_thermique": "baisse",
        "essences_hotes": ["prairie"],
        "altitude_max": 1800,
    },
    {
        "id": "coprin_chevelu",
        "nom": "Coprin chevelu",
        "nom_scientifique": "Coprinus comatus",
        "mois_actifs": [5, 6, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.5, 7.8),
        "temp_sol_optimale": (7.0, 15.0),
        "temp_sol_limites": (3.0, 20.0),
        "pluie_20j_optimale_mm": (30.0, 95.0),
        "delai_maturation_jours": (3, 8),
        "choc_thermique": "baisse",
        "essences_hotes": ["prairie", "lisière"],
        "altitude_max": 1800,
    },
    {
        "id": "marasme_oreades",
        "nom": "Marasme des Oréades (Faux mousseron)",
        "nom_scientifique": "Marasmius oreades",
        "mois_actifs": [5, 6, 7, 8, 9, 10, 11],
        "mois_optimaux": [6, 9, 10, 11],
        "ph_optimal": (5.2, 7.5),
        "temp_sol_optimale": (8.0, 19.0),
        "temp_sol_limites": (3.5, 24.0),
        "pluie_20j_optimale_mm": (30.0, 90.0),
        "delai_maturation_jours": (3, 8),
        "choc_thermique": "modere",
        "essences_hotes": ["prairie"],
        "altitude_max": 1800,
    },

    # --- MORILLES (PRINTEMPS) ---
    {
        "id": "morille_commune",
        "nom": "Morille commune",
        "nom_scientifique": "Morchella esculenta",
        "mois_actifs": [3, 4, 5],
        "mois_optimaux": [4, 5],
        "ph_optimal": (6.2, 8.0),
        "temp_sol_optimale": (8.0, 15.0),
        "temp_sol_limites": (5.0, 19.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "hausse",
        "essences_hotes": ["frêne", "orme", "peuplier", "noisetier", "charme", "feuillus", "sapin"],
        "altitude_max": 1800,
    },
    {
        "id": "morille_conique",
        "nom": "Morille conique (Morille noire)",
        "nom_scientifique": "Morchella elata",
        "mois_actifs": [3, 4, 5, 6],
        "mois_optimaux": [4, 5],
        "ph_optimal": (5.2, 7.5),
        "temp_sol_optimale": (7.0, 14.0),
        "temp_sol_limites": (4.0, 18.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "hausse",
        "essences_hotes": ["sapin", "épicéa", "pin", "conifères", "frêne"],
        "altitude_max": 2200,
    },

    # --- ESPÈCES CONTEXTUELLES ÉTENDUES (PRINTEMPS, HIVER, MONTAGNE, MIDI) ---
    {
        "id": "morille_ronde",
        "nom": "Morille ronde (Morille blonde)",
        "nom_scientifique": "Morchella rotunda",
        "mois_actifs": [3, 4, 5],
        "mois_optimaux": [4, 5],
        "ph_optimal": (6.5, 8.2),
        "temp_sol_optimale": (8.5, 16.0),
        "temp_sol_limites": (5.0, 20.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "hausse",
        "essences_hotes": ['frêne', 'orme', 'pommier', 'peuplier', 'noisetier', 'lisière', 'verger'],
        "altitude_max": 1800,
        "ecoregions": ['generaliste', 'continental', 'montagne'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "morille_semi_libre",
        "nom": "Morillon semi-libre",
        "nom_scientifique": "Mitrophora semilibera",
        "mois_actifs": [3, 4, 5],
        "mois_optimaux": [4, 5],
        "ph_optimal": (6.2, 7.8),
        "temp_sol_optimale": (8.0, 15.0),
        "temp_sol_limites": (4.5, 19.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "hausse",
        "essences_hotes": ['frêne', 'peuplier', 'noisetier', 'saule', 'aubépine', 'lisière'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "pezize_veinee",
        "nom": "Pézize veinée (Oreille de cochon)",
        "nom_scientifique": "Disciotis venosa",
        "mois_actifs": [3, 4, 5],
        "mois_optimaux": [4, 5],
        "ph_optimal": (6.5, 8.2),
        "temp_sol_optimale": (7.5, 15.0),
        "temp_sol_limites": (4.0, 19.0),
        "pluie_20j_optimale_mm": (30.0, 80.0),
        "delai_maturation_jours": (5, 10),
        "choc_thermique": "hausse",
        "essences_hotes": ['frêne', 'hêtre', 'peuplier', 'orme', 'prairie', 'lisière'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental', 'montagne'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "hygrophore_mars",
        "nom": "Hygrophore de mars (Marzœul)",
        "nom_scientifique": "Hygrophorus marzuolus",
        "mois_actifs": [2, 3, 4, 5],
        "mois_optimaux": [3, 4],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (3.0, 10.0),
        "temp_sol_limites": (0.0, 14.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (7, 15),
        "choc_thermique": "hausse",
        "essences_hotes": ['sapin', 'épicéa', 'hêtre', 'pin', 'conifères'],
        "altitude_min": 500,
        "altitude_max": 2000,
        "ecoregions": ['montagne'],
        "cryophile": True,
    },
    {
        "id": "polypore_ecailleux",
        "nom": "Polypore écailleux",
        "nom_scientifique": "Cerioporus squamosus",
        "mois_actifs": [4, 5, 6, 9, 10],
        "mois_optimaux": [4, 5],
        "ph_optimal": (5.5, 7.5),
        "temp_sol_optimale": (10.0, 19.0),
        "temp_sol_limites": (6.0, 24.0),
        "pluie_20j_optimale_mm": (30.0, 90.0),
        "delai_maturation_jours": (4, 9),
        "choc_thermique": "modere",
        "essences_hotes": ['frêne', 'érable', 'hêtre', 'saule', 'peuplier', 'orme', 'noyer'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental'],
        "type_trophique": "lignicole",
    },
    {
        "id": "flammuline_pied_veloute",
        "nom": "Flammuline à pied velouté (Collybie)",
        "nom_scientifique": "Flammulina velutipes",
        "mois_actifs": [10, 11, 12, 1, 2, 3],
        "mois_optimaux": [11, 12, 1, 2],
        "ph_optimal": (5.0, 7.8),
        "temp_sol_optimale": (1.0, 8.0),
        "temp_sol_limites": (-3.0, 13.0),
        "pluie_20j_optimale_mm": (25.0, 85.0),
        "delai_maturation_jours": (4, 10),
        "choc_thermique": "baisse",
        "essences_hotes": ['saule', 'peuplier', 'orme', 'frêne', 'sureau', 'hêtre', 'érable'],
        "altitude_max": 1800,
        "ecoregions": ['generaliste', 'continental', 'montagne'],
        "type_trophique": "lignicole",
        "cryophile": True,
    },
    {
        "id": "oreille_de_judas",
        "nom": "Oreille-de-Judas",
        "nom_scientifique": "Auricularia auricula-judae",
        "mois_actifs": [9, 10, 11, 12, 1, 2, 3, 4],
        "mois_optimaux": [11, 12, 1, 2],
        "ph_optimal": (5.5, 7.8),
        "temp_sol_optimale": (3.0, 12.0),
        "temp_sol_limites": (-2.0, 18.0),
        "pluie_20j_optimale_mm": (30.0, 95.0),
        "delai_maturation_jours": (4, 10),
        "choc_thermique": "baisse",
        "essences_hotes": ['sureau', 'frêne', 'érable', 'saule', 'hêtre', 'orme', 'robinier'],
        "altitude_max": 1800,
        "ecoregions": ['generaliste', 'continental', 'atlantique'],
        "type_trophique": "lignicole",
        "cryophile": True,
    },
    {
        "id": "hygrophore_des_neiges",
        "nom": "Hygrophore blanc des neiges",
        "nom_scientifique": "Cuphophyllus virgineus",
        "mois_actifs": [10, 11, 12, 1],
        "mois_optimaux": [11, 12],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (3.0, 11.0),
        "temp_sol_limites": (-1.0, 16.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['prairie', 'pelouse', 'lisière'],
        "altitude_max": 2000,
        "ecoregions": ['generaliste', 'montagne', 'continental'],
        "type_trophique": "saprophyte",
        "cryophile": True,
    },
    {
        "id": "tricholome_pretentieux",
        "nom": "Tricholome prétentieux (Charbonnier)",
        "nom_scientifique": "Tricholoma portentosum",
        "mois_actifs": [10, 11, 12],
        "mois_optimaux": [10, 11, 12],
        "ph_optimal": (4.2, 6.5),
        "temp_sol_optimale": (3.5, 11.0),
        "temp_sol_limites": (-1.0, 15.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['pin', 'épicéa', 'sapin', 'hêtre', 'conifères'],
        "altitude_max": 1900,
        "ecoregions": ['montagne', 'continental', 'atlantique'],
        "cryophile": True,
    },
    {
        "id": "hygrophore_limace",
        "nom": "Hygrophore limace (Hygrophore d'or)",
        "nom_scientifique": "Hygrophorus hypothejus",
        "mois_actifs": [10, 11, 12],
        "mois_optimaux": [11, 12],
        "ph_optimal": (4.0, 6.2),
        "temp_sol_optimale": (2.5, 9.5),
        "temp_sol_limites": (-2.0, 14.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['pin', 'conifères'],
        "altitude_max": 2000,
        "ecoregions": ['montagne', 'atlantique', 'continental'],
        "cryophile": True,
    },
    {
        "id": "pleurote_panicaut",
        "nom": "Pleurote du panicaut (Argouane)",
        "nom_scientifique": "Pleurotus eryngii",
        "mois_actifs": [4, 5, 10, 11, 12],
        "mois_optimaux": [4, 5, 10, 11],
        "ph_optimal": (6.5, 8.5),
        "temp_sol_optimale": (10.0, 18.0),
        "temp_sol_limites": (4.0, 23.0),
        "pluie_20j_optimale_mm": (30.0, 85.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ['prairie', 'pelouse', 'garrigue', 'causses'],
        "altitude_max": 1400,
        "ecoregions": ['mediterraneen', 'generaliste'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "chanterelle_subpruineuse",
        "nom": "Chanterelle pruineuse (Chanterelle du Midi)",
        "nom_scientifique": "Cantharellus subpruinosus",
        "mois_actifs": [5, 6, 9, 10, 11],
        "mois_optimaux": [5, 6, 10],
        "ph_optimal": (5.2, 7.5),
        "temp_sol_optimale": (11.0, 20.0),
        "temp_sol_limites": (6.0, 25.0),
        "pluie_20j_optimale_mm": (40.0, 115.0),
        "delai_maturation_jours": (8, 16),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'châtaignier', 'hêtre', 'charme', 'feuillus'],
        "altitude_max": 1200,
        "ecoregions": ['mediterraneen', 'generaliste'],
    },
    {
        "id": "bolet_appendicule",
        "nom": "Bolet appendiculé",
        "nom_scientifique": "Butyriboletus appendiculatus",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [7, 8, 9],
        "ph_optimal": (6.0, 7.8),
        "temp_sol_optimale": (13.0, 21.0),
        "temp_sol_limites": (8.0, 26.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'hêtre', 'châtaignier', 'feuillus'],
        "altitude_max": 1300,
        "ecoregions": ['mediterraneen', 'generaliste'],
    },
    {
        "id": "bolet_regius",
        "nom": "Cèpe royal (Bolet royal)",
        "nom_scientifique": "Butyriboletus regius",
        "mois_actifs": [6, 7, 8, 9],
        "mois_optimaux": [7, 8],
        "ph_optimal": (5.5, 7.5),
        "temp_sol_optimale": (15.0, 23.0),
        "temp_sol_limites": (10.0, 27.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'châtaignier', 'hêtre', 'feuillus'],
        "altitude_max": 1200,
        "ecoregions": ['mediterraneen', 'generaliste'],
    },
    {
        "id": "bolet_depoli",
        "nom": "Bolet dépoli",
        "nom_scientifique": "Hemileccinum depilatum",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [7, 8, 9],
        "ph_optimal": (6.2, 7.8),
        "temp_sol_optimale": (13.0, 21.0),
        "temp_sol_limites": (8.0, 25.0),
        "pluie_20j_optimale_mm": (35.0, 95.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'charme', 'hêtre', 'feuillus'],
        "altitude_max": 1300,
        "ecoregions": ['mediterraneen', 'generaliste'],
    },
    {
        "id": "lactaire_quieticolor",
        "nom": "Lactaire gris-orangé (Catalan de plaine)",
        "nom_scientifique": "Lactarius quieticolor",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (8.0, 16.0),
        "temp_sol_limites": (3.5, 20.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ['pin', 'conifères'],
        "altitude_max": 1500,
        "ecoregions": ['mediterraneen', 'atlantique'],
    },
    {
        "id": "sarcodon_imbrique",
        "nom": "Hydne imbriqué (Écailleux des sapins)",
        "nom_scientifique": "Sarcodon imbricatus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.0, 6.2),
        "temp_sol_optimale": (6.0, 13.5),
        "temp_sol_limites": (2.0, 17.0),
        "pluie_20j_optimale_mm": (45.0, 120.0),
        "delai_maturation_jours": (8, 16),
        "choc_thermique": "baisse",
        "essences_hotes": ['épicéa', 'sapin', 'pin', 'conifères'],
        "altitude_min": 600,
        "altitude_max": 2200,
        "ecoregions": ['montagne'],
    },
    {
        "id": "lactaire_epicea",
        "nom": "Lactaire de l'épicéa",
        "nom_scientifique": "Lactarius deterrimus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.5, 7.2),
        "temp_sol_optimale": (6.5, 14.0),
        "temp_sol_limites": (2.0, 18.0),
        "pluie_20j_optimale_mm": (40.0, 115.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ['épicéa', 'conifères'],
        "altitude_min": 500,
        "altitude_max": 2200,
        "ecoregions": ['montagne'],
    },
    {
        "id": "lactaire_saumon",
        "nom": "Lactaire saumon (Lactaire du sapin)",
        "nom_scientifique": "Lactarius salmonicolor",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (6.5, 14.5),
        "temp_sol_limites": (2.0, 18.0),
        "pluie_20j_optimale_mm": (40.0, 115.0),
        "delai_maturation_jours": (6, 13),
        "choc_thermique": "baisse",
        "essences_hotes": ['sapin', 'conifères'],
        "altitude_min": 400,
        "altitude_max": 1900,
        "ecoregions": ['montagne'],
    },
    {
        "id": "gomphide_luisant",
        "nom": "Gomphide luisant (Clou de girofle)",
        "nom_scientifique": "Chroogomphus rutilus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.5, 7.5),
        "temp_sol_optimale": (6.5, 14.5),
        "temp_sol_limites": (2.0, 18.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['pin', 'conifères'],
        "altitude_max": 2000,
        "ecoregions": ['montagne', 'generaliste'],
    },
    {
        "id": "hygrophore_pudibond",
        "nom": "Hygrophore pudibond",
        "nom_scientifique": "Hygrophorus erubescens",
        "mois_actifs": [8, 9, 10],
        "mois_optimaux": [9, 10],
        "ph_optimal": (6.0, 7.8),
        "temp_sol_optimale": (6.5, 13.5),
        "temp_sol_limites": (2.0, 17.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ['épicéa', 'sapin', 'conifères'],
        "altitude_min": 600,
        "altitude_max": 2000,
        "ecoregions": ['montagne'],
    },
    {
        "id": "bolet_granule",
        "nom": "Bolet granulé (Pissacan)",
        "nom_scientifique": "Suillus granulatus",
        "mois_actifs": [5, 6, 7, 8, 9, 10, 11],
        "mois_optimaux": [6, 7, 9, 10],
        "ph_optimal": (5.0, 7.8),
        "temp_sol_optimale": (9.0, 18.0),
        "temp_sol_limites": (4.0, 23.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['pin', 'conifères'],
        "altitude_max": 2000,
        "ecoregions": ['mediterraneen', 'atlantique', 'montagne', 'generaliste'],
    },
    {
        "id": "suillus_grevillei",
        "nom": "Bolet du mélèze (Bolet élégant)",
        "nom_scientifique": "Suillus grevillei",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 7.2),
        "temp_sol_optimale": (7.5, 16.0),
        "temp_sol_limites": (3.0, 20.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['mélèze', 'conifères'],
        "altitude_min": 400,
        "altitude_max": 2300,
        "ecoregions": ['montagne'],
    },
    {
        "id": "bolet_pruineux",
        "nom": "Bolet pruineux",
        "nom_scientifique": "Xerocomellus pruinatus",
        "mois_actifs": [8, 9, 10, 11, 12],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (6.0, 15.0),
        "temp_sol_limites": (2.0, 19.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['hêtre', 'chêne', 'épicéa', 'sapin', 'feuillus', 'conifères'],
        "altitude_max": 2000,
        "ecoregions": ['generaliste', 'montagne', 'continental'],
    },
    {
        "id": "cortinaire_remarquable",
        "nom": "Cortinaire remarquable (Gros pied)",
        "nom_scientifique": "Cortinarius praestans",
        "mois_actifs": [8, 9, 10],
        "mois_optimaux": [9, 10],
        "ph_optimal": (6.5, 8.0),
        "temp_sol_optimale": (8.5, 16.5),
        "temp_sol_limites": (4.0, 21.0),
        "pluie_20j_optimale_mm": (40.0, 115.0),
        "delai_maturation_jours": (7, 14),
        "choc_thermique": "baisse",
        "essences_hotes": ['hêtre', 'chêne', 'charme', 'feuillus'],
        "altitude_max": 1400,
        "ecoregions": ['generaliste', 'continental'],
    },
    {
        "id": "lepiote_mamelonnee",
        "nom": "Lépiote mamelonnée",
        "nom_scientifique": "Macrolepiota mastoidea",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (7.0, 16.5),
        "temp_sol_limites": (2.5, 21.0),
        "pluie_20j_optimale_mm": (30.0, 95.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'hêtre', 'châtaignier', 'feuillus', 'pin', 'lisière', 'prairie'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'atlantique', 'mediterraneen'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "clitocybe_nebuleux",
        "nom": "Clitocybe nébuleux (Gris de sapin)",
        "nom_scientifique": "Lepista nebularis",
        "mois_actifs": [10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (4.5, 7.2),
        "temp_sol_optimale": (4.0, 12.5),
        "temp_sol_limites": (0.5, 16.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['hêtre', 'chêne', 'épicéa', 'sapin', 'feuillus', 'conifères'],
        "altitude_max": 1800,
        "ecoregions": ['generaliste', 'montagne', 'continental'],
        "type_trophique": "saprophyte",
        "cryophile": True,
    },
    {
        "id": "clitocybe_anis",
        "nom": "Clitocybe odorant (Odeur d'anis)",
        "nom_scientifique": "Clitocybe odora",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (7.0, 16.0),
        "temp_sol_limites": (2.5, 20.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['hêtre', 'chêne', 'conifères', 'feuillus'],
        "altitude_max": 1800,
        "ecoregions": ['generaliste', 'continental'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "tricholome_colombette",
        "nom": "Tricholome colombette (Jument blanche)",
        "nom_scientifique": "Tricholoma columbetta",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10],
        "ph_optimal": (4.2, 6.2),
        "temp_sol_optimale": (7.5, 16.5),
        "temp_sol_limites": (3.0, 20.0),
        "pluie_20j_optimale_mm": (35.0, 105.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['chêne', 'hêtre', 'châtaignier', 'bouleau', 'feuillus'],
        "altitude_max": 1500,
        "ecoregions": ['generaliste', 'atlantique'],
    },
    {
        "id": "russule_violine",
        "nom": "Russule belette (Russule jolie)",
        "nom_scientifique": "Russula mustelina",
        "mois_actifs": [7, 8, 9, 10],
        "mois_optimaux": [8, 9],
        "ph_optimal": (4.2, 6.0),
        "temp_sol_optimale": (8.0, 16.0),
        "temp_sol_limites": (3.5, 20.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['épicéa', 'sapin', 'hêtre', 'conifères'],
        "altitude_min": 600,
        "altitude_max": 2200,
        "ecoregions": ['montagne'],
    },
    {
        "id": "russule_vesca",
        "nom": "Russule comestible (Russule pudique)",
        "nom_scientifique": "Russula vesca",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [6, 7, 9],
        "ph_optimal": (4.5, 6.8),
        "temp_sol_optimale": (9.0, 18.0),
        "temp_sol_limites": (4.5, 23.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'hêtre', 'châtaignier', 'pin', 'feuillus', 'conifères'],
        "altitude_max": 1700,
        "ecoregions": ['generaliste', 'continental', 'atlantique'],
    },
    {
        "id": "russule_integra",
        "nom": "Russule entière (Russule des sapins)",
        "nom_scientifique": "Russula integra",
        "mois_actifs": [7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (4.5, 7.2),
        "temp_sol_optimale": (7.0, 15.5),
        "temp_sol_limites": (2.5, 19.0),
        "pluie_20j_optimale_mm": (40.0, 110.0),
        "delai_maturation_jours": (6, 12),
        "choc_thermique": "baisse",
        "essences_hotes": ['épicéa', 'sapin', 'pin', 'conifères'],
        "altitude_min": 500,
        "altitude_max": 2200,
        "ecoregions": ['montagne'],
    },
    {
        "id": "tricholome_scalpturatum",
        "nom": "Tricholome gravé (Petit gris jaunissant)",
        "nom_scientifique": "Tricholoma scalpturatum",
        "mois_actifs": [9, 10, 11, 12],
        "mois_optimaux": [10, 11],
        "ph_optimal": (5.5, 7.8),
        "temp_sol_optimale": (5.0, 13.0),
        "temp_sol_limites": (1.0, 17.0),
        "pluie_20j_optimale_mm": (35.0, 100.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "baisse",
        "essences_hotes": ['chêne', 'bouleau', 'peuplier', 'tilleul', 'lisière', 'parcs'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental', 'atlantique'],
    },
    {
        "id": "chanterelle_cineree",
        "nom": "Chanterelle cendrée",
        "nom_scientifique": "Craterellus cinereus",
        "mois_actifs": [8, 9, 10, 11],
        "mois_optimaux": [9, 10, 11],
        "ph_optimal": (5.0, 7.5),
        "temp_sol_optimale": (7.0, 15.0),
        "temp_sol_limites": (3.0, 19.0),
        "pluie_20j_optimale_mm": (50.0, 130.0),
        "delai_maturation_jours": (7, 15),
        "choc_thermique": "baisse",
        "essences_hotes": ['hêtre', 'chêne', 'charme', 'feuillus'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental'],
    },
    {
        "id": "vesse_de_loup_geante",
        "nom": "Vesse-de-loup géante",
        "nom_scientifique": "Calvatia gigantea",
        "mois_actifs": [6, 7, 8, 9, 10, 11],
        "mois_optimaux": [8, 9, 10],
        "ph_optimal": (5.5, 7.8),
        "temp_sol_optimale": (8.5, 18.0),
        "temp_sol_limites": (4.0, 23.0),
        "pluie_20j_optimale_mm": (30.0, 90.0),
        "delai_maturation_jours": (4, 9),
        "choc_thermique": "modere",
        "essences_hotes": ['prairie', 'verger', 'lisière'],
        "altitude_max": 1600,
        "ecoregions": ['generaliste', 'continental', 'atlantique'],
        "type_trophique": "saprophyte",
    },
    {
        "id": "bolet_chataignier",
        "nom": "Bolet châtain",
        "nom_scientifique": "Gyroporus castaneus",
        "mois_actifs": [6, 7, 8, 9, 10],
        "mois_optimaux": [7, 8, 9],
        "ph_optimal": (4.5, 6.5),
        "temp_sol_optimale": (13.0, 21.0),
        "temp_sol_limites": (8.0, 25.0),
        "pluie_20j_optimale_mm": (30.0, 95.0),
        "delai_maturation_jours": (5, 11),
        "choc_thermique": "modere",
        "essences_hotes": ['chêne', 'châtaignier', 'hêtre', 'feuillus'],
        "altitude_max": 1400,
        "ecoregions": ['generaliste', 'atlantique', 'mediterraneen'],
    },
]


def _score_intervalle(valeur, opt_min, opt_max, lim_min, lim_max):
    """
    Renvoie un score entre 0.0 et 1.0 :
    - 1.0 si valeur est dans [opt_min, opt_max]
    - décroissance linéaire vers 0.0 entre opt et lim
    - 0.0 hors de [lim_min, lim_max]
    """
    if valeur is None:
        return 0.5
    if opt_min <= valeur <= opt_max:
        return 1.0
    if valeur < lim_min or valeur > lim_max:
        return 0.0
    if valeur < opt_min:
        return (valeur - lim_min) / max(0.01, (opt_min - lim_min))
    return (lim_max - valeur) / max(0.01, (lim_max - opt_max))


# =====================================================================
# MODULE DE VIGILANCE MYCOLOGIQUE & RISQUES DE CONFUSION TOXICOLOGIQUE
# =====================================================================
CONFUSIONS_TOXIQUES = {
    "agaric_bois": {
        "toxique": "Amanite phalloïde / printanière (Amanita phalloides, verna)",
        "gravite": "MORTEL",
        "critere_cle": "L'amanite mortelle possède des lames d'un BLANC IMMACULÉ et une VOLVE en sac à la base du pied enfoui. L'agaric comestible a des lames rosées puis brun chocolat et aucune volve.",
        "icone": "☠️",
        "securisant": False,
    },
    "rose_des_pres": {
        "toxique": "Amanite phalloïde & Agaric jaunissant (Agaricus xanthodermus)",
        "gravite": "MORTEL / TOXIQUE",
        "critere_cle": "Rejeter impérativement tout champignon blanc à lames blanches (amanite) ou jaunissant vivement au frottement à la base du pied avec odeur désagréable d'encre/iode (agaric jaunissant).",
        "icone": "☠️",
        "securisant": False,
    },
    "coulemelle": {
        "toxique": "Petites Lépiotes mortelles (Lepiota brunneoincarnata, helveola, cristata)",
        "gravite": "MORTEL",
        "critere_cle": "Règle absolue du mycologue : NE JAMAIS ramasser de lépiote dont le chapeau fait moins de 10-12 cm de diamètre. La vraie coulemelle est géante, son pied est chiné comme une peau de serpent et son anneau est double et coulissant.",
        "icone": "☠️",
        "securisant": False,
    },
    "lepiote_mamelonnee": {
        "toxique": "Petites Lépiotes mortelles du groupe brunneoincarnata",
        "gravite": "MORTEL",
        "critere_cle": "Rejeter systématiquement tout spécimen de petite taille (< 10 cm). Anneau coulissant et pied chiné obligatoires.",
        "icone": "☠️",
        "securisant": False,
    },
    "girolle": {
        "toxique": "Clitocybe de l'olivier (Omphalotus illudens) & Fausse girolle",
        "gravite": "TRÈS TOXIQUE",
        "critere_cle": "La vraie girolle pousse au sol, a de la chair blanche et possède des PLIS (replis de chair non détachables), jamais de vraies lames serrées. Le clitocybe de l'olivier pousse en touffes serrées au pied ou sur souches de feuillus.",
        "icone": "⚠️",
        "securisant": False,
    },
    "chanterelle_cineree": {
        "toxique": "Clitocybe de l'olivier ou fausses chanterelles",
        "gravite": "TOXIQUE",
        "critere_cle": "Présence de plis ramifiés gris cendré sous le chapeau creux. Chair mince et odeur fruitée agréable.",
        "icone": "⚠️",
        "securisant": False,
    },
    "cepe_bordeaux": {
        "toxique": "Bolet amer (Tylopilus felleus) & Bolet de Satan (Rubroboletus satanas)",
        "gravite": "INDIGESTION SÉVÈRE / TRÈS AMER",
        "critere_cle": "Le cèpe de Bordeaux a des pores fins blancs devenant jaune-verdâtre (jamais rouge vif), et un fin réseau blanc au sommet du pied. Le bolet de Satan a un pied renflé rouge sang.",
        "icone": "⚠️",
        "securisant": False,
    },
    "bolet_bai": {
        "toxique": "Bolet amer (Tylopilus felleus)",
        "gravite": "AMER IMMANGEABLE",
        "critere_cle": "Les pores du bolet bai bleuissent légèrement au doigt. Le bolet amer a des pores rosâtres à maturité et un gros réseau noir saillant sur le pied.",
        "icone": "⚠️",
        "securisant": False,
    },
    "tricholome_terreux": {
        "toxique": "Tricholome tigré (Tricholoma pardinum) & Inocybes toxiques",
        "gravite": "TRÈS TOXIQUE",
        "critere_cle": "Le petit gris comestible est frêle, sans anneau, chapeau feutré-souris, pousse sous pins. Le tricholome tigré est trapu, gros pied renflé, grosses écailles brunes, surtout en montagne calcaire.",
        "icone": "⚠️",
        "securisant": False,
    },
    "pied_bleu": {
        "toxique": "Cortinaires violets à cortine rouille (Cortinarius violaceus, purpurascens)",
        "gravite": "INDIGESTION",
        "critere_cle": "Le pied bleu a une sporée rose-crème et aucune cortine filamenteuse ni résidu rouille. Odeur fruitée caractéristique de bonbon/anisette.",
        "icone": "⚠️",
        "securisant": False,
    },
    "pleurote_huitre": {
        "toxique": "Pleurote de l'olivier (Omphalotus olearius)",
        "gravite": "TRÈS TOXIQUE",
        "critere_cle": "Le pleurote en huître sort de novembre à février par temps froid, de couleur gris plomb à beige. Le pleurote de l'olivier est orange vif à jaune cuivré et pousse en été/automne.",
        "icone": "⚠️",
        "securisant": False,
    },
    "morille_commune": {
        "toxique": "Gyromitre fausse-morille (Gyromitra esculenta)",
        "gravite": "MORTEL CRU",
        "critere_cle": "La vraie morille a un chapeau creux alvéolé en rayons de miel, soudé au pied. Le gyromitre a un chapeau cérébriforme (en cervelle) brun-rouge. Toutes les morilles doivent impérativement être cuites au moins 20 minutes !",
        "icone": "☠️",
        "securisant": False,
    },
    "lactaire_delicieux": {
        "toxique": "Lactaires à lait blanc très âcres (Lactarius torminosus, etc.)",
        "gravite": "GASTRO-ENTÉRITE VIOLENTE",
        "critere_cle": "Les lactaires comestibles saignent TOUJOURS d'un lait orange vif ou rouge sang à la cassure (jamais blanc). Poussent sous pins.",
        "icone": "⚠️",
        "securisant": False,
    },
    "marasme_oreades": {
        "toxique": "Petits Clitocybes blancs des pelouses (Clitocybe rivulosa, cerussata)",
        "gravite": "TRÈS TOXIQUE (Syndrome muscarinien)",
        "critere_cle": "Le faux mousseron a un pied élastique imputrescible que l'on peut tordre sans le casser, des lames très espacées et une odeur d'amande amère.",
        "icone": "⚠️",
        "securisant": False,
    },
    "pied_de_mouton": {
        "toxique": "Aucune confusion mortelle connue en Europe",
        "gravite": "COMESTIBLE REMARQUABLE SANS RISQUE",
        "critere_cle": "Unique grâce à ses aiguillons fragiles sous le chapeau qui se détachent facilement au doigt. Aucune espèce à aiguillons n'est toxique.",
        "icone": "🛡️",
        "securisant": True,
    },
    "pied_de_mouton_roussissant": {
        "toxique": "Aucune confusion mortelle",
        "gravite": "COMESTIBLE EXCELLENT SANS RISQUE",
        "critere_cle": "Aiguillons bien visibles non décurrents, silhouette plus rousse et plus grêle que le grand pied-de-mouton.",
        "icone": "🛡️",
        "securisant": True,
    },
    "trompette_mort": {
        "toxique": "Aucune confusion mortelle (Espèce signature)",
        "gravite": "COMESTIBLE EXCELLENT SANS RISQUE",
        "critere_cle": "Entonnoir entièrement creux noir à gris cendré, hyménium lisse ou très légèrement veiné. Impossible à confondre.",
        "icone": "🛡️",
        "securisant": True,
    },
    "chanterelle_tube": {
        "toxique": "Aucune confusion dangereuse",
        "gravite": "COMESTIBLE DÉLICIEUX SANS DANGER",
        "critere_cle": "Pied tubulaire creux jaune vif éclatant, chapeau brun percé au centre, plis espacés décurrents.",
        "icone": "🛡️",
        "securisant": True,
    },
    "sparassis_crepu": {
        "toxique": "Aucune confusion mortelle",
        "gravite": "COMESTIBLE EXCELLENT SANS RISQUE",
        "critere_cle": "Forme d'éponge ou d'énorme chou-fleur frisé au pied des vieux pins.",
        "icone": "🛡️",
        "securisant": True,
    },
    "oreille_de_judas": {
        "toxique": "Aucune confusion mortelle",
        "gravite": "COMESTIBLE SÛR",
        "critere_cle": "Consistance gélatineuse en forme d'oreille humaine, pousse quasi-exclusivement sur bois mort de sureau.",
        "icone": "🛡️",
        "securisant": True,
    },
}

def obtenir_confusion_toxique(espece_id):
    """Renvoie la fiche de vigilance toxicologique contextuelle d'une espèce."""
    cle = str(espece_id).strip().lower()
    if cle in CONFUSIONS_TOXIQUES:
        return CONFUSIONS_TOXIQUES[cle]
    for k, val in CONFUSIONS_TOXIQUES.items():
        if k in cle or cle in k:
            return val
    return {
        "toxique": "Espèces voisines toxiques à vérifier en cas de doute",
        "gravite": "VIGILANCE",
        "critere_cle": "Toujours faire contrôler sa récolte auprès d'un pharmacien ou d'une société mycologique en cas de spécimen atypique.",
        "icone": "ℹ️",
        "securisant": False,
    }


# Groupes trophiques des espèces du catalogue :
# - "lignicole" : pousse sur le bois (troncs, souches, racines) -> très peu dépendant du pH du sol minéral,
#                 mais 100 % dépendant de la présence de l'arbre hôte.
# - "saprophyte" : décompose l'humus, la litière ou l'herbe morte -> sensible au pH de l'humus et au couvert.
# - "mycorhizien" : symbiose obligatoire avec les racines d'un arbre hôte ET sensible au pH du sol.
ESPECES_LIGNICOLES = {
    "fistuline_hepatique",
    "poule_des_bois",
    "polypore_soufre",
    "sparassis_crepu",
    "pleurote_huitre",
    "pholiote_peuplier",
    "polypore_ecailleux",
    "flammuline_pied_veloute",
    "oreille_de_judas",
    "lentin_chene",
    "hydne_herisson",
}

ESPECES_SAPROPHYTES = {
    "pied_bleu",
    "mousseron_st_georges",
    "tete_de_moine",
    "coulemelle",
    "agaric_bois",
    "rose_des_pres",
    "coprin_chevelu",
    "marasme_oreades",
    "morille_commune",
    "morille_conique",
    "morille_ronde",
    "morille_semi_libre",
    "pezize_veinee",
    "hygrophore_des_neiges",
    "pleurote_panicaut",
    "vesse_de_loup_geante",
    "clitocybe_nebuleux",
    "clitocybe_anis",
    "agaric_forets",
    "lepiote_excoriee",
}


def _type_trophique_espece(espece):
    esp_id = espece["id"]
    if espece.get("type_trophique") == "lignicole" or esp_id in ESPECES_LIGNICOLES:
        return "lignicole"
    if espece.get("type_trophique") == "saprophyte" or esp_id in ESPECES_SAPROPHYTES:
        return "saprophyte"
    return "mycorhizien"


def evaluer_biotope(espece, profil_env):
    """
    Calcule le score de compatibilité écologique (forêt/habitat × sol/pH × topographie) entre 0.0 et 1.0 :
    1. L'adéquation de l'habitat (arbre hôte mycorhizien/lignicole ou prairie) agit comme un facteur
       multiplicatif strict : sans l'arbre hôte (ou en futaie fermée pour une espèce prairiale comme
       le Marasme des Oréades ou le Rosé des prés), le score chute près de 0 %.
    2. Le pH du sol agit selon le type trophique :
       - Espèces terrestres (mycorhiziennes et saprophytes) : tolérance resserrée (±0.75 u. pH) et
         effet limitant multiplicatif (une espèce calcicole comme la Tête de moine ne fructifie pas
         sur un sol acide de châtaigneraie à pH 5.2).
       - Espèces lignicoles (Fistuline, Poule des bois, Pleurote...) : poussent sur le bois, donc
         très peu sensibles au pH minéral du sol mais strictement liées à l'essence hôte.
    """
    sol = profil_env.get("sol", {})
    foret = profil_env.get("foret", {})
    topo = profil_env.get("topographie", {})
    altitude = profil_env.get("altitude_m") or topo.get("altitude_m") or 200.0
    pente_deg = topo.get("pente_deg", 0.0) or 0.0
    type_trophique = _type_trophique_espece(espece)

    # 1. Score pH du sol (marge resserrée à ±0.75 unité pH hors de la plage optimale)
    ph = sol.get("ph")
    ph_min, ph_max = espece["ph_optimal"]
    score_ph = _score_intervalle(ph, ph_min, ph_max, ph_min - 0.75, ph_max + 0.75)

    # 2. Score habitat & essence forestière hôte (BD Forêt IGN)
    peuplements = foret.get("peuplements", [])
    en_lisiere = foret.get("en_lisiere", False)
    peuplements_lisiere = foret.get("peuplements_lisiere", [])
    hotes = espece["essences_hotes"]
    est_espece_prairiale_stricte = set(hotes) <= {"prairie", "lisière"}

    if not peuplements:
        # Zone hors polygone forestier IGN (prairie, pâture, pelouse ou lisière bordière)
        if en_lisiere and peuplements_lisiere:
            texte_lisiere = " ".join(
                f"{p.get('formation_vegetale', '')} {p.get('essence', '')}"
                for p in peuplements_lisiere
            ).lower()
            corresp_lisiere = [
                h for h in hotes if h not in ("prairie", "lisière") and h in texte_lisiere
            ]
            if "prairie" in hotes or "lisière" in hotes:
                score_foret = 1.0  # Lisière herbeuse : optimal pour Coulemelle, Marasme, Coprin, Tête de moine
            elif corresp_lisiere:
                score_foret = 0.65  # Racines mycorhiziennes de la lisière adjacente (< 25 m)
            else:
                score_foret = 0.12
        else:
            # Pleine prairie (> 25 m de tout boisement)
            if "prairie" in hotes:
                score_foret = 1.0  # Habitat optimal pour Marasme des Oréades, Rosé des prés, Coulemelle, Coprin
            elif "lisière" in hotes:
                score_foret = 0.65
            else:
                score_foret = 0.10  # Espèce strictement forestière en plein pré ouvert
    else:
        texte_foret = " ".join(
            f"{p.get('formation_vegetale', '')} {p.get('essence', '')}"
            for p in peuplements
        ).lower()
        en_foret_fermee = "fermée" in texte_foret

        if est_espece_prairiale_stricte:
            if en_foret_fermee:
                # Le Marasme des Oréades et le Rosé des prés ne poussent pas sous futaie fermée (châtaigniers, hêtres...)
                score_foret = 0.02 if "lisière" not in hotes else 0.12
            else:
                # Forêt ouverte / clairière herbeuse / lande
                score_foret = 0.45
        else:
            correspondances = [h for h in hotes if h not in ("prairie", "lisière") and h in texte_foret]
            peuplement_melange_feuillus = any(
                "feuillus" in p.get("formation_vegetale", "").lower()
                and "pur" not in p.get("formation_vegetale", "").lower()
                for p in peuplements
            )
            if any(h not in ("feuillus", "conifères") for h in correspondances):
                score_foret = 1.0  # Essence hôte exacte présente (ex: Châtaignier, Hêtre, Chêne, Pin)
            elif correspondances:
                score_foret = 0.85  # Catégorie forestière compatible (ex: mélange de feuillus / conifères)
            elif peuplement_melange_feuillus and any(
                h in ("bouleau", "peuplier", "frêne", "charme", "noisetier", "saule", "orme", "hêtre") for h in hotes
            ):
                # Dans un "mélange de feuillus" non pur, présence possible d'essences secondaires (hêtre, charme, bouleau...)
                score_foret = 0.45
            else:
                # Arbre hôte absent du peuplement (ex: espèce des pins sous châtaignier pur)
                score_foret = 0.04

    # 3. Score altitude & pente topographique
    alt_max = espece["altitude_max"]
    score_alt = 1.0 if altitude <= alt_max else max(0.0, 1.0 - (altitude - alt_max) / 500.0)
    score_pente = 1.0 if pente_deg <= 22.0 else max(0.3, 1.0 - (pente_deg - 22.0) / 30.0)
    score_topo = 0.70 * score_alt + 0.30 * score_pente

    # 4. Combinaison écologique selon le groupe trophique :
    if type_trophique == "lignicole":
        # Espèce lignicole : dépend de l'arbre hôte et de la topographie, peu du pH du sol minéral
        facteur_edaphique = 0.22 * score_ph + 0.78 * score_topo
    else:
        # Espèce terrestre (mycorhizienne ou saprophyte) : le pH est un facteur limitant multiplicatif
        facteur_edaphique = score_ph * (0.35 + 0.65 * score_topo)

    return round(score_foret * facteur_edaphique, 3)


def _duree_croissance_base_carpophore(espece):
    """
    Renvoie la durée nominale (en jours, à température et humidité optimales)
    pour qu'un primordium devienne un champignon adulte récoltable, selon le groupe fongique.
    """
    esp_id = espece["id"]
    # Espèces à croissance ultra-rapide (1 à 3 jours)
    if esp_id in ("coprin_chevelu", "rose_des_pres", "marasme_oreades", "coulemelle", "agaric_bois"):
        return 2.0
    # Espèces à croissance lente et charnue/coriace (7 à 12 jours)
    if esp_id in (
        "girolle",
        "trompette_mort",
        "chanterelle_tube",
        "chanterelle_jaunissante",
        "pied_de_mouton",
        "pied_de_mouton_roussissant",
        "poule_des_bois",
        "fistuline_hepatique",
        "polypore_soufre",
        "sparassis_crepu",
    ):
        return 8.0
    # Cèpes, Bolets, Amanites, Russules, Lactaires, Tricholomes, Morilles (3 à 5 jours)
    return 4.0


def _persistance_volee_carpophore(espece):
    """
    Durée moyenne (en jours) pendant laquelle une volée de carpophores adultes reste récoltable
    sur pied en forêt (tant qu'il ne gèle pas et que le sol ne sèche pas).
    """
    esp_id = espece["id"]
    if esp_id in (
        "coprin_chevelu",
        "rose_des_pres",
        "amanite_rougissante",
        "amanite_vaginee",
        "meunier",
        "marasme_oreades",
        "agaric_bois",
        "morille_ronde",
        "morille_semi_libre",
        "pezize_veinee",
    ):
        return 3
    if esp_id in (
        "girolle",
        "trompette_mort",
        "chanterelle_tube",
        "chanterelle_jaunissante",
        "pied_de_mouton",
        "pied_de_mouton_roussissant",
        "poule_des_bois",
        "fistuline_hepatique",
        "polypore_soufre",
        "sparassis_crepu",
        "pleurote_huitre",
        "polypore_ecailleux",
        "flammuline_pied_veloute",
        "oreille_de_judas",
        "hydne_herisson",
        "sarcodon_imbrique",
        "chanterelle_cineree",
        "chanterelle_subpruineuse",
    ):
        return 8
    # Cèpes, Bolets, Coulemelles, Russules, Lactaires, Tricholomes, Laccaire
    return 6


# Espèces à mycélium superficiel (litière de feuilles 0-2 cm / mousses) ou à primordia fins/lents
# qui avortent rapidement si la litière superficielle sèche pendant 6 à 10 jours sans pluie :
ESPECES_SENSIBLES_SECHERESSE_LITIERE = {
    "trompette_mort",
    "chanterelle_tube",
    "chanterelle_jaunissante",
    "girolle",
    "pied_de_mouton",
    "pied_de_mouton_roussissant",
    "laccaire_amethyste",
    "laccaire_laque",
    "marasme_oreades",
    "rose_des_pres",
    "coprin_chevelu",
    "vesse_de_loup",
}

# Espèces exigeant une saturation hydrique profonde et continue de l'humus sur 35 à 45 jours
# (très sensibles aux sécheresses de fin d'été / début d'automne ; ne sortent jamais sur une seule pluie isolée) :
ESPECES_EXIGEANTES_SATURATION_PROFONDE = {
    "trompette_mort",
    "girolle",
    "pied_de_mouton",
    "pied_de_mouton_roussissant",
    "chanterelle_tube",
    "chanterelle_jaunissante",
    "tete_de_moine",
    "pied_bleu",
}

# Espèces cryophiles dont la fructification est stimulée par les premières gelées blanches (-2.5°C à +2°C)
ESPECES_CRYOPHILES_GEL = {
    "pied_bleu",
    "chanterelle_tube",
    "chanterelle_jaunissante",
    "pleurote_huitre",
    "tricholome_terreux",
    "tete_de_moine",
    "pied_de_mouton_roussissant",
    "hygrophore_mars",
    "flammuline_pied_veloute",
    "oreille_de_judas",
    "hygrophore_des_neiges",
    "tricholome_pretentieux",
    "hygrophore_limace",
    "clitocybe_nebuleux",
}

# Espèces estivales et de début d'automne frileuses (arrêt net si nuits froides <= 2.0°C ou gelées blanches)
ESPECES_THERMOPHILES_SENSIBLES_FROID = {
    "amanite_rougissante",
    "amanite_vaginee",
    "amanite_cesars",
    "cepe_ete",
    "cepe_bronze",
    "russule_charbonniere",
    "russule_verdoyante",
    "russule_doree",
    "polypore_soufre",
    "fistuline_hepatique",
    "bolet_pied_rouge",
    "meunier",
}


def _extraire_parametres_edaphiques_et_canopee(profil_env):
    """
    Déduit de la texture du sol (sable/argile) et du couvert forestier IGN (Forêt fermée vs ouverte) :
    - Le niveau de protection de la canopée (interception des bruines, réduction du vent et de l'ET0,
      amortissement du gel nocturne sous bois).
    - Le comportement hydrique et thermique du sol lié à sa texture (drainage sableux vs rétention argileuse).
    """
    if not profil_env:
        return {
            "couvert": "Ouvert",
            "coeff_vent_sous_bois": 1.0,
            "coeff_et0_sous_bois": 1.0,
            "tampon_gel_c": 0.0,
            "interception_bruine_ratio": 1.0,
            "coeff_retention_texture": 1.0,
            "coeff_inertie_maturation": 1.0,
            "risque_asphyxie_argile": False,
        }

    sol = profil_env.get("sol", {}) or {}
    foret = profil_env.get("foret", {}) or {}
    topo = profil_env.get("topographie", {}) or {}

    peuplements = foret.get("peuplements", [])
    en_lisiere = foret.get("en_lisiere", False)
    texte_foret = " ".join(p.get("formation_vegetale", "") for p in peuplements).lower()

    if "fermée" in texte_foret:
        couvert = "Forêt fermée (canopée dense)"
        coeff_vent_sous_bois = 0.38   # Le vent est freiné de >60% au ras du sol
        coeff_et0_sous_bois = 0.58    # L'évapotranspiration sous canopée est réduite de ~42%
        tampon_gel_c = 2.0            # Le houppier et la litière amortissent le gel nocturne de +2°C
        interception_bruine_ratio = 0.35  # Les petites bruines (<2mm) mouillent les feuilles sans atteindre le sol
    elif peuplements:
        couvert = "Forêt ouverte / Boisement"
        coeff_vent_sous_bois = 0.65
        coeff_et0_sous_bois = 0.78
        tampon_gel_c = 1.0
        interception_bruine_ratio = 0.65
    elif en_lisiere:
        dist_m = foret.get("distance_foret_m")
        couvert = f"Prairie en lisière de bois ({dist_m} m)" if dist_m is not None else "Prairie en lisière de bois"
        coeff_vent_sous_bois = 0.78
        coeff_et0_sous_bois = 0.88
        tampon_gel_c = 0.6
        interception_bruine_ratio = 0.90
    else:
        couvert = "Milieu ouvert / Prairie (Hors forêt)"
        coeff_vent_sous_bois = 1.0
        coeff_et0_sous_bois = 1.0
        tampon_gel_c = 0.0
        interception_bruine_ratio = 1.0

    sable = sol.get("sable_pct") or 35.0
    argile = sol.get("argile_pct") or 20.0
    pente_deg = topo.get("pente_deg") or 0.0

    # Texture sableuse (>55% sable) : réchauffement rapide (maturation -12%), mais sèche plus vite (-10%)
    if sable >= 55.0:
        coeff_retention_texture = 0.90
        coeff_inertie_maturation = 0.88
        risque_asphyxie_argile = False
    # Texture argileuse (>30% argile) : forte rétention d'eau (+12%), réchauffement lent (+8%), risque d'asphyxie sur plat
    elif argile >= 30.0:
        coeff_retention_texture = 1.12
        coeff_inertie_maturation = 1.08
        risque_asphyxie_argile = pente_deg < 3.5
    else:
        coeff_retention_texture = 1.0
        coeff_inertie_maturation = 1.0
        risque_asphyxie_argile = False

    return {
        "couvert": couvert,
        "coeff_vent_sous_bois": coeff_vent_sous_bois,
        "coeff_et0_sous_bois": coeff_et0_sous_bois,
        "tampon_gel_c": tampon_gel_c,
        "interception_bruine_ratio": interception_bruine_ratio,
        "coeff_retention_texture": coeff_retention_texture,
        "coeff_inertie_maturation": coeff_inertie_maturation,
        "risque_asphyxie_argile": risque_asphyxie_argile,
    }


def calculer_cinetique_pousse(
    espece,
    temps_sol,
    humidites_sol,
    index_jour,
    coeff_inertie_maturation=1.0,
    coeff_assechement_air=1.0,
):
    """
    Calcule dynamiquement en fonction des conditions météo, de la texture du sol et du dessèchement éolien :
    1. Le délai de maturation mycélienne effectif (en jours entre la pluie déclenchante et l'émergence)
       modulé par la température/humidité du sol sur les 12 derniers jours et l'inertie sable/argile,
       ainsi que la fenêtre de persistance de la volée sur pied.
    2. La vitesse de pousse du carpophore (en % de la vitesse optimale et en nombre de jours
       nécessaires pour atteindre la taille adulte) en fonction de la température, de l'humidité du sol
       et de l'assèchement de l'air (vent / ET0 / humidité relative).
    """
    d_min, d_max = espece["delai_maturation_jours"]
    t_opt_min, t_opt_max = espece["temp_sol_optimale"]
    t_lim_min, t_lim_max = espece["temp_sol_limites"]

    # Température et humidité moyennes du sol sur les 12 jours précédant index_jour (incubation mycélienne)
    fenetre_incub = [
        t for t in temps_sol[max(0, index_jour - 12) : index_jour + 1] if t is not None
    ]
    t_incub = sum(fenetre_incub) / len(fenetre_incub) if fenetre_incub else (t_opt_min + t_opt_max) / 2.0

    fenetre_hum_incub = [
        h for h in humidites_sol[max(0, index_jour - 12) : index_jour + 1] if h is not None
    ]
    h_incub = sum(fenetre_hum_incub) / len(fenetre_hum_incub) if fenetre_hum_incub else 0.25

    # Facteur thermique d'incubation (0.0 = froid limite -> délai max, 1.0 = chaud optimal -> délai min)
    if t_incub >= t_opt_max:
        ratio_temp_incub = 1.0
    elif t_incub <= t_lim_min:
        ratio_temp_incub = 0.0
    else:
        ratio_temp_incub = (t_incub - t_lim_min) / max(0.5, (t_opt_max - t_lim_min))

    ratio_hum_incub = _score_intervalle(h_incub, 0.24, 0.42, 0.10, 0.55)
    ratio_vitesse_incub = ratio_temp_incub * (0.35 + 0.65 * ratio_hum_incub)

    # Délai effectif de fructification modulé par l'inertie thermique du sol (sable plus rapide, argile plus lente)
    delai_central = (d_max - ratio_vitesse_incub * (d_max - d_min)) * coeff_inertie_maturation
    delai_central = max(2.0, min(20.0, delai_central))
    marge_avant = max(2.0, (d_max - d_min) * 0.45)
    persistance_j = _persistance_volee_carpophore(espece)
    delai_debut = int(round(max(2.0, delai_central - marge_avant)))
    delai_fin = int(round(min(20.0, delai_central + persistance_j)))

    # Vitesse de pousse du carpophore au jour J+k (turgescence = T° sol 3j * humidité sol 3j * hygrométrie air/vent)
    fenetre_t3 = [t for t in temps_sol[max(0, index_jour - 2) : index_jour + 1] if t is not None]
    t_actuel = sum(fenetre_t3) / len(fenetre_t3) if fenetre_t3 else t_incub

    fenetre_h3 = [h for h in humidites_sol[max(0, index_jour - 2) : index_jour + 1] if h is not None]
    h_actuel = sum(fenetre_h3) / len(fenetre_h3) if fenetre_h3 else 0.25

    coeff_temp_pousse = _score_intervalle(t_actuel, t_opt_min, t_opt_max, t_lim_min, t_lim_max)
    coeff_hum_pousse = _score_intervalle(h_actuel, 0.22, 0.42, 0.11, 0.55)

    # Vitesse relative de croissance du champignon (0.0 à 1.0)
    vitesse_relative = round(
        min(1.0, coeff_temp_pousse * coeff_hum_pousse * coeff_assechement_air), 2
    )
    duree_base = _duree_croissance_base_carpophore(espece)

    if coeff_temp_pousse < 0.08:
        jours_croissance = None
        qualificatif_vitesse = "Bloquée (froid/chaud)"
    elif coeff_hum_pousse < 0.10 or coeff_assechement_air < 0.25:
        jours_croissance = None
        qualificatif_vitesse = "Bloquée (sécheresse/vent)"
    else:
        jours_croissance = round(duree_base / max(0.20, vitesse_relative), 1)
        if vitesse_relative >= 0.80:
            qualificatif_vitesse = f"Rapide (~{jours_croissance} j)"
        elif vitesse_relative >= 0.45:
            qualificatif_vitesse = f"Modérée (~{jours_croissance} j)"
        else:
            qualificatif_vitesse = f"Ralentie (~{jours_croissance} j)"

    return {
        "delai_maturation_effectif_j": round(delai_central, 1),
        "fenetre_induction_j": (delai_debut, delai_fin),
        "temp_incubation_12j_c": round(t_incub, 1),
        "vitesse_pousse_pct": int(round(vitesse_relative * 100)),
        "jours_croissance_carpophore": jours_croissance,
        "qualificatif_vitesse": qualificatif_vitesse,
    }


def _calculer_stades_maturite_carpophore(
    precips_efficaces,
    index_jour,
    d_debut,
    delai_central,
    d_fin,
    coeff_assechement_air=1.0,
    facteur_gel=1.0,
):
    """
    Détermine la répartition probable des stades de développement des carpophores sur le terrain
    au jour `index_jour` en fonction de l'âge des pluies déclenchantes (entre J-20 et J) :
    - 🌱 En pousse (jeunes boutons / bouchons en émergence)
    - 🍄 Adultes (carpophores à pleine maturité, fermes)
    - 🍂 Vieillissants (carpophores avancés / fin de volée)
    ou une combinaison de ces stades (ex: En pousse & Adultes, Adultes & Vieillissants, Double volée...).
    """
    persistance = max(2.0, d_fin - delai_central)
    debut_20j = max(0, index_jour - 20)

    somme_jeunes = 0.0
    somme_adultes = 0.0
    somme_vieux = 0.0

    for idx_p in range(debut_20j, index_jour + 1):
        p_eff = precips_efficaces[idx_p - debut_20j]
        if p_eff <= 0.1:
            continue
        age_j = float(index_jour - idx_p)

        w_jeune = _score_intervalle(
            age_j,
            max(1.5, d_debut - 0.3),
            delai_central + 0.10 * persistance,
            max(1.0, d_debut - 1.8),
            delai_central + 0.42 * persistance,
        )
        w_adulte = _score_intervalle(
            age_j,
            delai_central + 0.12 * persistance,
            delai_central + 0.62 * persistance,
            max(1.5, delai_central - 1.0),
            delai_central + 0.90 * persistance,
        )
        w_vieux = _score_intervalle(
            age_j,
            delai_central + 0.68 * persistance,
            d_fin + 0.8,
            delai_central + 0.38 * persistance,
            min(22.0, d_fin + 3.2),
        )

        somme_jeunes += p_eff * w_jeune
        somme_adultes += p_eff * w_adulte
        somme_vieux += p_eff * w_vieux

    # Accélération du vieillissement par le vent sec ou le gel
    if coeff_assechement_air < 0.55 and somme_adultes > 0:
        transfert_sec = somme_adultes * (0.55 - coeff_assechement_air) * 0.75
        somme_adultes = max(0.0, somme_adultes - transfert_sec)
        somme_vieux += transfert_sec

    if facteur_gel < 0.60 and somme_adultes > 0:
        transfert_gel = somme_adultes * 0.45
        somme_adultes = max(0.0, somme_adultes - transfert_gel)
        somme_vieux += transfert_gel

    total = somme_jeunes + somme_adultes + somme_vieux
    if total <= 0.25:
        return {
            "en_pousse_pct": 0,
            "adultes_pct": 0,
            "vieillissants_pct": 0,
            "icone": "—",
            "label_court": "Aucune volée active",
            "diagnostic": "Aucune volée active",
        }

    pct_j = int(round(100.0 * somme_jeunes / total))
    pct_a = int(round(100.0 * somme_adultes / total))
    pct_v = max(0, 100 - pct_j - pct_a)

    seuil_combinaison = 24
    if pct_j >= seuil_combinaison and pct_a >= seuil_combinaison and pct_v >= seuil_combinaison:
        icone = "🌱🍄🍂"
        label_court = "En pousse, Adultes & Vieillissants"
    elif pct_j >= 58:
        icone = "🌱"
        label_court = "En pousse (jeunes)"
    elif pct_a >= 58:
        icone = "🍄"
        label_court = "Adultes (pleine maturité)"
    elif pct_v >= 58:
        icone = "🍂"
        label_court = "Vieillissants (fin de volée)"
    elif pct_j >= seuil_combinaison and pct_a >= seuil_combinaison:
        icone = "🌱🍄"
        label_court = "En pousse & Adultes"
    elif pct_a >= seuil_combinaison and pct_v >= seuil_combinaison:
        icone = "🍄🍂"
        label_court = "Adultes & Vieillissants"
    elif pct_j >= seuil_combinaison and pct_v >= seuil_combinaison:
        icone = "🌱🍂"
        label_court = "Double volée (En pousse & Vieillissants)"
    elif pct_j >= pct_a and pct_j >= pct_v:
        icone = "🌱"
        label_court = "En pousse (jeunes)"
    elif pct_a >= pct_j and pct_a >= pct_v:
        icone = "🍄"
        label_court = "Adultes (pleine maturité)"
    else:
        icone = "🍂"
        label_court = "Vieillissants (fin de volée)"

    diagnostic = (
        f"{icone} {label_court} "
        f"({pct_j}% en pousse • {pct_a}% adultes • {pct_v}% vieillissants)"
    )

    return {
        "en_pousse_pct": pct_j,
        "adultes_pct": pct_a,
        "vieillissants_pct": pct_v,
        "icone": icone,
        "label_court": label_court,
        "diagnostic": diagnostic,
    }


def calculer_score_jour(espece, meteo, index_jour, score_biotope, topographie=None, profil_env=None):
    """
    Calcule le score de fructification (0 à 100 %) pour une espèce donnée au jour `index_jour`
    en distinguant les deux phases biologiques du cycle fongique :
    - Phase A (Induction & Maturation mycélienne, de J-20 à J-d_debut) :
      Pluie infiltrée pendant la fenêtre d'induction + persistance de la volée sur pied,
      effet Birch (réveil après sécheresse), choc thermique et température d'incubation sur 12 jours.
    - Phase B (Émergence, Croissance & Maintien des carpophores sur pied, de J-3 à J) :
      Humidité superficielle du sol (0-7 cm), vent sous couvert, humidité de l'air, ET0,
      et survie au gel nocturne sous canopée.
    """
    topo = topographie or (profil_env.get("topographie") if profil_env else None) or {}
    params_eco = _extraire_parametres_edaphiques_et_canopee(profil_env)

    delta_temp_expo = topo.get("delta_temp_sol_c", 0.0) or 0.0
    coeff_ret_hum = (topo.get("coeff_retention_humidite", 1.0) or 1.0) * params_eco["coeff_retention_texture"]
    coeff_infilt_pluie = topo.get("coeff_infiltration_pluie", 1.0) or 1.0

    dates = meteo.get("time", [])
    precips = meteo.get("precipitation_sum", [])
    temps_sol_brut = (
        meteo.get("soil_temperature_6cm")
        or meteo.get("soil_temperature_0cm")
        or meteo.get("temperature_2m_mean", [])
    )
    humidites_sol_brut = meteo.get("soil_moisture_0_to_7cm", [])
    temps_min_air = meteo.get("temperature_2m_min", [])
    vents_max = meteo.get("wind_speed_10m_max", [])
    et0_serie = meteo.get("et0_fao_evapotranspiration", [])
    hr_air_serie = meteo.get("relative_humidity_2m", [])

    date_str = dates[index_jour]
    mois = int(date_str.split("-")[1])

    # Effet isolant de la litière forestière (humus/feuilles mortes) et du tapis herbacé en automne/hiver :
    # À 6-12 cm sous l'humus en futaie fermée, le sol reste ~+2.0°C plus doux qu'un sol agricole nu
    bonus_humus_automne = (
        max(0.8, params_eco["tampon_gel_c"] * 1.05) if mois in (10, 11, 12, 1, 2, 3) else 0.0
    )

    # Application des modificateurs microclimatiques liés à l'orientation (Adret/Ubac), à l'humus et au sol
    serie_temp_sol = [
        round(t + delta_temp_expo + bonus_humus_automne, 2) if t is not None else None
        for t in temps_sol_brut
    ]
    humidites_sol = [
        round(h * coeff_ret_hum, 3) if h is not None else None for h in humidites_sol_brut
    ]

    # 1. Facteur de saisonnalité
    if mois in espece["mois_optimaux"]:
        facteur_saison = 1.0
    elif mois in espece["mois_actifs"]:
        facteur_saison = 0.75
    else:
        return {
            "date": date_str,
            "score_pct": 0,
            "details": {
                "pluie_20j_mm": 0.0,
                "pluie_maturation_mm": 0.0,
                "temp_sol_c": serie_temp_sol[index_jour] if index_jour < len(serie_temp_sol) else None,
                "humidite_sol_m3": humidites_sol[index_jour] if index_jour < len(humidites_sol) else None,
                "delai_maturation_j": None,
                "vitesse_pousse": "Hors saison",
            },
        }

    # 2. Vent, Humidité relative de l'air & Évapotranspiration (ET0) sous couvert sur 3 jours
    fenetre_vent = [
        v * params_eco["coeff_vent_sous_bois"]
        for v in vents_max[max(0, index_jour - 2) : index_jour + 1]
        if v is not None
    ]
    vent_effectif_kmh = round(sum(fenetre_vent) / len(fenetre_vent), 1) if fenetre_vent else 10.0

    fenetre_et0 = [
        e * params_eco["coeff_et0_sous_bois"]
        for e in et0_serie[max(0, index_jour - 2) : index_jour + 1]
        if e is not None
    ]
    et0_effectif_mm = round(sum(fenetre_et0) / len(fenetre_et0), 2) if fenetre_et0 else 1.2

    fenetre_hr = [
        hr for hr in hr_air_serie[max(0, index_jour - 2) : index_jour + 1] if hr is not None
    ]
    hr_moy_pct = round(sum(fenetre_hr) / len(fenetre_hr), 1) if fenetre_hr else 78.0

    # Calcul du facteur d'assèchement / hygrométrie de l'air (vent sec vs brouillard forestier calme)
    score_vent = _score_intervalle(vent_effectif_kmh, 0.0, 14.0, 0.0, 38.0)
    score_et0 = _score_intervalle(et0_effectif_mm, 0.0, 1.8, 0.0, 4.5)
    score_hr_air = _score_intervalle(hr_moy_pct, 75.0, 100.0, 42.0, 100.0)
    coeff_assechement_air = round(0.40 * score_hr_air + 0.35 * score_vent + 0.25 * score_et0, 2)

    # 3. Cinétique dynamique de maturation et de pousse selon la météo, la texture du sol et le vent
    cinetique = calculer_cinetique_pousse(
        espece,
        serie_temp_sol,
        humidites_sol,
        index_jour,
        coeff_inertie_maturation=params_eco["coeff_inertie_maturation"],
        coeff_assechement_air=max(0.30, coeff_assechement_air),
    )
    d_debut, d_fin = cinetique["fenetre_induction_j"]

    # 4. Précipitations efficaces (filtrées par l'interception foliaire des bruines et le ruissellement de pente)
    def _pluie_efficace_sol(p_brute):
        p = p_brute or 0.0
        if p <= 0.0:
            return 0.0
        # Les petites bruines (< 2 mm) sont partiellement retenues par le houppier en forêt fermée
        if p < 2.0:
            p = p * params_eco["interception_bruine_ratio"]
        elif params_eco["interception_bruine_ratio"] < 0.5:
            p = p * 0.88  # Interception foliaire classique (~12%) sur pluie franche en futaie fermée
        return p * coeff_infilt_pluie

    debut_20j = max(0, index_jour - 20)
    fenetre_pluie = [_pluie_efficace_sol(p) for p in precips[debut_20j : index_jour + 1]]
    cumul_20j = round(sum(fenetre_pluie), 1)

    # Phase A : Pluie tombée AVANT l'émergence pondérée par la courbe de réponse mycélienne (émergence -> pic -> persistance)
    # Une pluie tombant le jour même (index_jour) ne fait pas pousser un cèpe instantanément si la forêt était sèche avant !
    delai_central = cinetique["delai_maturation_effectif_j"]
    pic_debut = max(1.5, delai_central - 1.0)
    pic_fin = delai_central + 0.45 * max(1.0, (d_fin - delai_central))
    age_min = max(1.0, d_debut - 1.5)
    age_max = min(21.0, d_fin + 2.0)

    def _poids_pluie_selon_age(age_j):
        if age_j < age_min or age_j > age_max:
            return 0.0
        if pic_debut <= age_j <= pic_fin:
            return 1.0
        if age_j < pic_debut:
            return (age_j - age_min) / max(0.5, (pic_debut - age_min))
        return (age_max - age_j) / max(0.5, (age_max - pic_fin))

    def _survie_cohorte_secheresse(idx_pluie):
        """
        Évalue la survie des primordia induits par la pluie du jour `idx_pluie` jusqu'au jour `index_jour`.
        Si une période sèche prolongée (>= 6 à 8 jours consécutifs < 1.2 mm) survient entre `idx_pluie + 1`
        et `index_jour`, la litière superficielle sèche et fait avorter les primordia de cette cohorte
        (qui ne ressuscitent pas même s'il repleut la veille de `index_jour`).
        """
        max_sec = 0
        sec_courant = 0
        for idx_k in range(idx_pluie + 1, index_jour + 1):
            if _pluie_efficace_sol(precips[idx_k]) < 1.2:
                sec_courant += 1
                if sec_courant > max_sec:
                    max_sec = sec_courant
            else:
                sec_courant = 0
        if espece["id"] in ESPECES_SENSIBLES_SECHERESSE_LITIERE:
            if max_sec >= 8:
                return 0.20
            if max_sec >= 5:
                return 0.50
        else:
            if max_sec >= 9:
                return 0.55
        return 1.0

    pluie_maturation = 0.0
    for idx_p in range(debut_20j, index_jour + 1):
        age_j = index_jour - idx_p
        poids = _poids_pluie_selon_age(age_j)
        if poids > 0.0:
            survie = _survie_cohorte_secheresse(idx_p)
            pluie_maturation += _pluie_efficace_sol(precips[idx_p]) * poids * survie
    pluie_maturation = round(pluie_maturation, 1)

    idx_mat_debut = max(0, index_jour - d_fin)
    idx_mat_fin = max(0, index_jour - 2)
    cumul_avant_emergence = round(
        sum(
            _pluie_efficace_sol(precips[idx_p]) * (0.25 + 0.75 * _survie_cohorte_secheresse(idx_p))
            for idx_p in range(debut_20j, idx_mat_fin)
        ),
        1,
    )

    p_opt_min, p_opt_max = espece["pluie_20j_optimale_mm"]
    score_cumul_20j = _score_intervalle(
        cumul_avant_emergence, p_opt_min * 0.80, p_opt_max, 8.0, p_opt_max + 90.0
    )
    score_maturation = _score_intervalle(
        pluie_maturation, p_opt_min * 0.48, p_opt_max * 0.85, 3.0, p_opt_max * 1.15
    )

    # Stress hydrique antérieur (« Réveil du mycélium » / Effet Birch) vs Déficit de saturation profonde :
    # Attention : un épisode pluvieux isolé après une longue sécheresse réveille les espèces opportunistes
    # (Bolet bai, Marasme, Rosé), mais est insuffisant pour les espèces exigeant une saturation profonde
    # de l'humus (Trompette de la mort, Girolle, Pied-de-mouton) qui subissent un dieback mycélien estival !
    pluie_avant_induction = sum(
        _pluie_efficace_sol(p) for p in precips[debut_20j:idx_mat_debut]
    )
    nb_jours_pluie_20j = sum(1 for p in fenetre_pluie if p >= 2.0)

    bonus_reveil_mycelien = 1.0
    if espece["id"] in ESPECES_EXIGEANTES_SATURATION_PROFONDE:
        # Ces espèces exigent un humus profondément réhydraté par plusieurs épisodes pluvieux :
        # Si le cumul 20j est inférieur au seuil optimal ou concentré sur <= 3 jours de pluie isolés,
        # le mycélium (affaibli par la sécheresse antérieure) ne fructifie pas.
        if cumul_20j < p_opt_min * 0.75 or nb_jours_pluie_20j <= 3:
            bonus_reveil_mycelien = 0.42
        elif cumul_20j < p_opt_min or nb_jours_pluie_20j <= 5:
            bonus_reveil_mycelien = 0.72
    else:
        if pluie_avant_induction < 12.0 and pluie_maturation >= p_opt_min * 0.45 and cumul_20j >= p_opt_min * 0.75:
            bonus_reveil_mycelien = 1.08

    if params_eco["risque_asphyxie_argile"] and cumul_20j > 135.0:
        bonus_reveil_mycelien = min(bonus_reveil_mycelien, 0.72)

    score_pluie = min(1.0, (0.42 * score_cumul_20j + 0.58 * score_maturation) * bonus_reveil_mycelien)

    # 5. Phase B : Humidité du sol (0-7 cm) ET humectation de la litière superficielle (0-2 cm)
    # Open-Meteo mesure l'humidité jusqu'à 7 cm (qui reste ~0.30 même après 10 jours sans pluie).
    # Or, 7 à 10 jours consécutifs sans pluie (< 1.5 mm/j) sèchent la litière de feuilles mortes (0-2 cm) :
    # - Les espèces de litière superficielle à primordia fins/lents (Trompette, Girolle, Pied-de-mouton) avortent.
    # - Les bolets déjà sortis 7 jours plus tôt survivent uniquement à l'état "Vieillissants" (fin de volée).
    pluie_8j_recents = sum(_pluie_efficace_sol(p) for p in precips[max(0, index_jour - 7) : index_jour + 1])
    jours_sans_pluie = 0
    for idx_sec in range(index_jour, debut_20j - 1, -1):
        if _pluie_efficace_sol(precips[idx_sec]) < 1.2:
            jours_sans_pluie += 1
        else:
            break

    facteur_litiere_surface = 1.0
    if espece["id"] in ESPECES_SENSIBLES_SECHERESSE_LITIERE:
        if jours_sans_pluie >= 8 and pluie_8j_recents < 3.0:
            facteur_litiere_surface = 0.48  # Litière de feuilles sèche depuis > 8 jours -> avortement des primordia
        elif jours_sans_pluie >= 5 and pluie_8j_recents < 5.0:
            facteur_litiere_surface = 0.70
    else:
        if jours_sans_pluie >= 9 and pluie_8j_recents < 2.0:
            facteur_litiere_surface = 0.82  # Fin de volée sèche : seuls persistent des spécimens âgés

    fenetre_hum = [
        h for h in humidites_sol[max(0, index_jour - 2) : index_jour + 1] if h is not None
    ]
    hum_moy = round(sum(fenetre_hum) / len(fenetre_hum), 3) if fenetre_hum else 0.25
    score_humidite_sol = _score_intervalle(hum_moy, 0.22, 0.42, 0.09, 0.55)
    score_humidite = (0.72 * score_humidite_sol + 0.28 * coeff_assechement_air) * facteur_litiere_surface

    # Facteur hydrique global (l'induction préalable ET le maintien de l'humidité de litière sont requis)
    score_hydrique = score_pluie * (0.30 + 0.70 * score_humidite) if (score_pluie < 0.35 or facteur_litiere_surface < 0.40) else (
        (0.55 * score_pluie + 0.45 * score_humidite) * min(1.0, facteur_litiere_surface * 1.15)
    )

    # 6. Température du sol (inertie thermique mycélienne sur 12 jours + maintien sur 3 jours)
    fenetre_temp_12j = [
        t for t in serie_temp_sol[max(0, index_jour - 11) : index_jour + 1]
        if t is not None
    ]
    fenetre_temp_3j = [
        t for t in serie_temp_sol[max(0, index_jour - 2) : index_jour + 1]
        if t is not None
    ]
    if fenetre_temp_12j and fenetre_temp_3j:
        # Pondère la chaleur d'incubation sur 12j (qui a induit la volée en place) et la T° actuelle sur 3j
        t_sol = round(
            0.65 * (sum(fenetre_temp_12j) / len(fenetre_temp_12j))
            + 0.35 * (sum(fenetre_temp_3j) / len(fenetre_temp_3j)),
            1,
        )
    elif fenetre_temp_12j:
        t_sol = round(sum(fenetre_temp_12j) / len(fenetre_temp_12j), 1)
    else:
        t_sol = None

    t_opt_min, t_opt_max = espece["temp_sol_optimale"]
    t_lim_min, t_lim_max = espece["temp_sol_limites"]
    score_temp = _score_intervalle(t_sol, t_opt_min, t_opt_max, t_lim_min, t_lim_max)

    # Température minimale nocturne sous couvert forestier sur les 3 derniers jours
    fenetre_tmin = [
        tmin + params_eco["tampon_gel_c"] + delta_temp_expo * 0.5
        for tmin in temps_min_air[max(0, index_jour - 2) : index_jour + 1]
        if tmin is not None
    ]
    tmin_sous_bois = round(min(fenetre_tmin), 1) if fenetre_tmin else (t_sol if t_sol is not None else 8.0)

    facteur_gel = 1.0
    if espece["id"] in ESPECES_CRYOPHILES_GEL:
        if -2.5 <= tmin_sous_bois <= 2.0:
            facteur_gel = 1.12  # Gelée blanche stimulante pour Pied bleu, Chanterelle en tube, Pleurote...
        elif tmin_sous_bois < -5.0:
            facteur_gel = 0.25  # Gel profond bloquant
    elif espece["id"] in ESPECES_THERMOPHILES_SENSIBLES_FROID:
        if tmin_sous_bois <= 0.0:
            facteur_gel = 0.08  # Arrêt létal pour espèces estivales
        elif tmin_sous_bois <= 2.0:
            facteur_gel = 0.22  # Blocage net sous 2°C (Golmotte, Russule charbonnière, Meunier...)
        elif tmin_sous_bois <= 4.5:
            facteur_gel = 0.55  # Ralentissement fort
    else:
        if tmin_sous_bois <= -3.0:
            facteur_gel = 0.08  # Gel fort létal pour les carpophores de Cèpes, Girolles, Coulemelles
        elif tmin_sous_bois <= -1.0:
            facteur_gel = 0.42  # Gelée sous bois abîmant les carpophores non cryophiles

    # Calcul du choc thermique autour du déclenchement mycélien
    serie_temp = [t if t is not None else 12.0 for t in serie_temp_sol]
    avant_choc = serie_temp[max(0, index_jour - d_fin - 4) : max(1, index_jour - d_debut)]
    apres_choc = serie_temp[max(0, index_jour - d_debut) : max(1, index_jour)]
    delta_temp = (
        (sum(apres_choc) / len(apres_choc)) - (sum(avant_choc) / len(avant_choc))
        if avant_choc and apres_choc
        else 0.0
    )

    bonus_choc = 0.75  # Neutre par défaut
    if espece["choc_thermique"] == "baisse":
        if -6.5 <= delta_temp <= -1.2:
            bonus_choc = 1.0  # Choc thermique froid idéal
        elif delta_temp < -6.5:
            bonus_choc = 0.80
        elif delta_temp > 2.5:
            bonus_choc = 0.55  # Réchauffement défavorable aux espèces d'automne
    elif espece["choc_thermique"] == "hausse":
        if 1.2 <= delta_temp <= 6.5:
            bonus_choc = 1.0  # Réchauffement printanier idéal
        elif delta_temp < -2.0:
            bonus_choc = 0.50

    score_thermique = min(1.0, score_temp * (0.78 + 0.22 * bonus_choc) * facteur_gel)

    # 7. Modèle bioclimatique multiplicatif complet :
    # Le biotope (score_biotope) agit comme un facteur multiplicatif direct : sans l'arbre hôte,
    # hors de son pH toléré ou hors de son habitat, l'espèce ne peut pas fructifier.
    facteur_biotope = score_biotope
    facteur_dessiccation = 0.35 + 0.65 * min(1.0, coeff_assechement_air * 1.15)
    facteur_limitant_eau = min(1.0, score_hydrique * 1.12) * facteur_dessiccation
    facteur_limitant_temp = min(1.0, score_temp * 1.25) * min(1.0, facteur_gel)

    score_final = (
        100.0
        * facteur_saison
        * facteur_biotope
        * facteur_limitant_eau
        * facteur_limitant_temp
        * (0.52 * score_hydrique + 0.48 * score_thermique)
    )
    score_pct_int = int(round(max(0.0, min(100.0, score_final))))

    stades_carpophore = _calculer_stades_maturite_carpophore(
        fenetre_pluie,
        index_jour,
        d_debut,
        delai_central,
        d_fin,
        coeff_assechement_air=coeff_assechement_air,
        facteur_gel=facteur_gel,
    )

    # Détection du nanisme hydrique / thermique d'élongation (ex: Coulemelles ou Bolets 2x plus petits
    # lorsque le bulbe/primordium a été induit par une pluie antérieure mais que l'élongation du pied
    # et l'ouverture du chapeau par turgescence se font sans eau libre >= 6 jours et/ou par sol froid) :
    if jours_sans_pluie >= 6 and pluie_8j_recents < 4.0:
        if t_sol < espece["temp_sol_optimale"][0]:
            note_gabarit = " • 📏 Petit gabarit (nanisme sec & froid)"
        else:
            note_gabarit = " • 📏 Petit gabarit (manque d'eau libre)"
        stades_carpophore["diagnostic"] += note_gabarit
        stades_carpophore["label_court"] += " • 📏 Petit gabarit"

    return {
        "date": date_str,
        "score_pct": score_pct_int,
        "details": {
            "pluie_20j_mm": cumul_20j,
            "pluie_maturation_mm": pluie_maturation,
            "temp_sol_c": t_sol,
            "tmin_sous_bois_c": tmin_sous_bois,
            "variation_thermique_c": round(delta_temp, 1),
            "humidite_sol_m3": hum_moy,
            "humidite_air_pct": hr_moy_pct,
            "vent_sous_bois_kmh": vent_effectif_kmh,
            "et0_sous_bois_mm": et0_effectif_mm,
            "delai_maturation_j": cinetique["delai_maturation_effectif_j"],
            "vitesse_pousse_pct": cinetique["vitesse_pousse_pct"],
            "jours_croissance_carpophore": cinetique["jours_croissance_carpophore"],
            "vitesse_pousse": cinetique["qualificatif_vitesse"],
            "stades_carpophore": stades_carpophore,
        },
    }


def selectionner_catalogue_contextuel(
    latitude: float,
    longitude: float,
    mois: int,
    altitude: float = 300.0,
    essences: list = None,
    nb_especes: int = 44,
):
    """
    Sélectionne dynamiquement les `nb_especes` (44 par défaut) les plus adaptées
    au contexte géographique, altitudinal, saisonnier et écologique du point d'intérêt,
    parmi le Catalogue Maître de 80 espèces :
    1. Saisonnalité (50 pts mois optimal, 35 pts mois actif, 15 pts mois immédiatement adjacent).
    2. Altitude et étage de végétation (25 pts dans l'optimum, avec pénalité linéaire hors étage).
    3. Écorégion biogéographique (Méditerranée, Atlantique, Montagne, Continental, Généraliste).
    4. Adéquation avec le biotope forestier et les essences hôtes locales (jusqu'à 20 pts).
    """
    essences = [e.lower() for e in (essences or [])]
    est_montagne = altitude >= 700.0
    est_medit = (latitude <= 44.2 and longitude >= 2.5) or (latitude <= 43.6)
    est_atlantique = (longitude <= -0.3 and 43.4 <= latitude <= 48.5)
    est_continental = (latitude >= 47.0 and longitude >= 4.5 and not est_montagne)

    scores = []
    for esp in CATALOGUE_ESPECES:
        # 1. Saison
        m_opt = esp.get("mois_optimaux", [])
        m_act = esp.get("mois_actifs", [])
        if mois in m_opt:
            sc_saison = 50.0
        elif mois in m_act:
            sc_saison = 35.0
        elif any((m - mois) % 12 in (1, 11) for m in m_act):
            sc_saison = 15.0
        else:
            sc_saison = 0.0

        # 2. Altitude
        alt_min = esp.get("altitude_min", 0)
        alt_max = esp.get("altitude_max", 2500)
        if alt_min <= altitude <= alt_max:
            sc_alt = 25.0
        elif altitude < alt_min:
            sc_alt = max(0.0, 25.0 - (alt_min - altitude) * 0.06)
        else:
            sc_alt = max(0.0, 25.0 - (altitude - alt_max) * 0.06)

        # 3. Écorégion
        tags = esp.get("ecoregions", ["generaliste"])
        sc_eco = 15.0
        if est_montagne and "montagne" in tags:
            sc_eco = 25.0
        elif est_medit and "mediterraneen" in tags:
            sc_eco = 25.0
        elif est_atlantique and "atlantique" in tags:
            sc_eco = 25.0
        elif est_continental and "continental" in tags:
            sc_eco = 22.0
        elif "generaliste" in tags:
            sc_eco = 18.0

        # Malus si exclusion géographique flagrante
        if not est_montagne and altitude < 450 and tags == ["montagne"]:
            sc_eco -= 18.0
        if latitude > 46.5 and tags == ["mediterraneen"]:
            sc_eco -= 22.0

        # 4. Hôtes / Habitats
        hotes = [h.lower() for h in esp.get("essences_hotes", [])]
        if essences:
            if any(h in e or e in h for h in hotes for e in essences):
                sc_hote = 20.0
            elif "prairie" in hotes or "lisière" in hotes:
                sc_hote = 14.0
            else:
                sc_hote = 5.0
        else:
            sc_hote = 15.0

        total = sc_saison + sc_alt + sc_eco + sc_hote
        scores.append((total, esp))

    scores.sort(key=lambda x: (x[0], x[1]["nom"]), reverse=True)
    return [esp for _, esp in scores[:nb_especes]]


def simuler_pousse_point_gps(latitude, longitude, past_days=20, forecast_days=11):
    """
    Exécute la simulation complète pour un point GPS :
    1. Récupère le profil environnemental (altitude, sol SoilGrids, essences IGN BD Forêt)
    2. Récupère la météo sur J-20 à J+10 (31 jours au total)
    3. Sélectionne les 44 espèces adaptées au contexte géographique, saisonnier et écologique
    4. Calcule les scores journaliers pour J, J+1, J+2, ..., J+10 (11 jours)
    """
    profil_env = recuperer_profil_environnemental(latitude, longitude)
    meteo = recuperer_donnees_meteo(
        latitude, longitude, past_days=past_days, forecast_days=forecast_days
    )
    if not meteo or not meteo.get("time"):
        raise RuntimeError("Impossible de récupérer les données météorologiques.")

    dates = meteo["time"]
    # L'indice de J (aujourd'hui) est égal à `past_days` (20)
    idx_aujourd_hui = past_days
    nb_jours_total = len(dates)

    # Mois principal (au jour J)
    mois_j = int(dates[idx_aujourd_hui].split("-")[1])
    altitude = (
        profil_env.get("altitude_m")
        or (profil_env.get("topographie") or {}).get("altitude_m")
        or 300.0
    )

    essences_observees = []
    foret = profil_env.get("foret") or {}
    for p in foret.get("peuplements", []):
        if p.get("essence"):
            essences_observees.append(p["essence"])
        if p.get("formation_vegetale"):
            essences_observees.append(p["formation_vegetale"])
    for p in foret.get("peuplements_lisiere", []):
        if p.get("essence"):
            essences_observees.append(p["essence"])
        if p.get("formation_vegetale"):
            essences_observees.append(p["formation_vegetale"])

    catalogue_actif = selectionner_catalogue_contextuel(
        latitude,
        longitude,
        mois_j,
        altitude=altitude,
        essences=essences_observees,
        nb_especes=44,
    )

    resultats_especes = []
    for espece in catalogue_actif:
        score_biotope = evaluer_biotope(espece, profil_env)
        previsions_11j = []

        for decalage in range(nb_jours_total - idx_aujourd_hui):
            idx = idx_aujourd_hui + decalage
            etiquette = "J" if decalage == 0 else f"J+{decalage}"
            res_jour = calculer_score_jour(
                espece,
                meteo,
                idx,
                score_biotope,
                topographie=profil_env.get("topographie"),
                profil_env=profil_env,
            )
            res_jour["echeance"] = etiquette
            previsions_11j.append(res_jour)

        score_j = previsions_11j[0]["score_pct"] if previsions_11j else 0
        score_max_10j = max((p["score_pct"] for p in previsions_11j), default=0)

        item_esp = {
            "id": espece["id"],
            "nom": espece["nom"],
            "nom_scientifique": espece["nom_scientifique"],
            "comestibilite": espece.get("comestibilite", "Comestible"),
            "compatibilite_biotope_pct": int(round(score_biotope * 100)),
            "score_actuel_J": score_j,
            "score_actuel_j": score_j,
            "score_max_J10": score_max_10j,
            "score_max_j10": score_max_10j,
            "courbe_J_a_J10": previsions_11j,
            "courbe_j_a_j10": previsions_11j,
            "espece": {
                "id": espece["id"],
                "nom": espece["nom"],
                "nom_scientifique": espece["nom_scientifique"],
                "comestibilite": espece.get("comestibilite", "Comestible"),
            },
            "aptitude_biotope": {
                "score_foret": score_biotope,
                "score_sol": score_biotope,
            },
            "confusion_toxique": obtenir_confusion_toxique(espece["id"]),
        }
        resultats_especes.append(item_esp)

    # Tri par score maximum sur la période J..J+10 décroissant
    resultats_especes.sort(
        key=lambda e: (e["score_max_J10"], e["score_actuel_J"]), reverse=True
    )

    profil_env["microclimat_canopee_sol"] = _extraire_parametres_edaphiques_et_canopee(profil_env)

    # Enrichissement du sol avec alias pour le frontend
    sol_env = profil_env.get("sol") or {}
    ph_val = sol_env.get("ph")
    if "ph_eau" not in sol_env:
        sol_env["ph_eau"] = ph_val
    if "classe_texture" not in sol_env:
        sol_env["classe_texture"] = sol_env.get("type_sol")
    if "qualificatif_ph" not in sol_env and ph_val is not None:
        sol_env["qualificatif_ph"] = (
            "Neutre" if 6.0 <= ph_val <= 7.3 else ("Acide" if ph_val < 6.0 else "Calcaire")
        )
    profil_env["sol"] = sol_env

    # Calcul des cumuls météo
    precips = meteo.get("precipitation_sum", [])
    cumul_20j = round(float(sum(precips[:idx_aujourd_hui + 1])), 1) if precips else 0.0
    cumul_10j = round(float(sum(precips[idx_aujourd_hui + 1:])), 1) if precips else 0.0

    # Construction du verdict du jour synthétique
    top_score_j = max((e["score_actuel_J"] for e in resultats_especes), default=0)
    top_3_j = sorted(resultats_especes, key=lambda e: e["score_actuel_J"], reverse=True)[:3]
    top_especes_j = [
        {
            "nom": e["nom"],
            "nom_scientifique": e["nom_scientifique"],
            "score": e["score_actuel_J"],
            "id": e["id"],
        }
        for e in top_3_j
    ]

    if top_score_j >= 75:
        qualif = "EXCELLENT"
        conseil = f"Excellentes conditions aujourd'hui ({cumul_20j} mm de pluie cumulée). Plusieurs espèces sont en pleine maturité !"
    elif top_score_j >= 45:
        qualif = "FAVORABLE"
        conseil = f"Conditions favorables avec des poussées actives ({cumul_20j} mm cumulés). Bonnes chances de cueillette en sous-bois abrités."
    elif top_score_j >= 25:
        qualif = "MODÉRÉ"
        conseil = f"Poussées localisées ou carpophores jeunes en cours de développement ({cumul_20j} mm). Surveillez les jours à venir."
    else:
        qualif = "CALME"
        conseil = "Activité mycélienne en attente d'une pluie stimulante. Consultez les prévisions sur 10 jours."

    verdict_du_jour = {
        "score_global_j": top_score_j,
        "qualificatif": qualif,
        "conseil": conseil,
        "top_especes_j": top_especes_j,
    }

    meteo_periode_dict = {
        "dates": dates,
        "index_aujourd_hui": idx_aujourd_hui,
        "cumul_pluie_20j": cumul_20j,
        "cumul_pluie_10j": cumul_10j,
        "precipitation_sum": meteo.get("precipitation_sum", []),
        "soil_temperature_0cm": meteo.get("soil_temperature_0cm", []),
        "soil_moisture_0_to_7cm": meteo.get("soil_moisture_0_to_7cm", []),
        "temperature_2m_min": meteo.get("temperature_2m_min", []),
        "wind_speed_10m_max": meteo.get("wind_speed_10m_max", []),
        "et0_fao_evapotranspiration": meteo.get("et0_fao_evapotranspiration", []),
        "relative_humidity_2m": meteo.get("relative_humidity_2m", []),
    }

    return {
        "date_simulation": dates[idx_aujourd_hui],
        "environnement": profil_env,
        "meteo_periode": meteo_periode_dict,
        "especes_probables": resultats_especes,
        "especes": resultats_especes,
        "verdict_du_jour": verdict_du_jour,
    }


def _adapter_meteo_altitude(meteo_ref, delta_alt_m):
    """
    Applique le gradient thermique adiabatique moyen (-0.65°C par +100 m d'altitude)
    aux séries de température du sol et de l'air minimale pour une zone située à
    `delta_alt_m` mètres au-dessus/en-dessous du point central.
    """
    if abs(delta_alt_m) < 12.0:
        return meteo_ref
    delta_t = round(-0.0065 * delta_alt_m, 2)
    copie = dict(meteo_ref)
    if "soil_temperature_0cm" in meteo_ref:
        copie["soil_temperature_0cm"] = [
            round(t + delta_t, 2) if t is not None else None
            for t in meteo_ref["soil_temperature_0cm"]
        ]
    if "temperature_2m_min" in meteo_ref:
        copie["temperature_2m_min"] = [
            round(t + delta_t, 2) if t is not None else None
            for t in meteo_ref["temperature_2m_min"]
        ]
    return copie


def _formater_libelle_biotope_zone(foret_zone):
    """Construit un libellé synthétique clair du biotope d'une zone."""
    if foret_zone.get("en_zone_boisee") and foret_zone.get("peuplements"):
        p0 = foret_zone["peuplements"][0]
        tfv = p0.get("formation_vegetale") or "Boisement"
        ess = p0.get("essence") or ""
        if ess and ess.lower() not in tfv.lower():
            return f"🌲 {tfv} ({ess})"
        return f"🌲 {tfv}"
    if foret_zone.get("en_lisiere") and foret_zone.get("peuplements_lisiere"):
        p0 = foret_zone["peuplements_lisiere"][0]
        ess = p0.get("essence") or p0.get("formation_vegetale") or "bois"
        return f"🌿 Prairie en lisière ({ess})"
    return "🌾 Prairie / Milieu ouvert (Hors forêt)"


def rechercher_zones_optimales_5km(
    latitude,
    longitude,
    espece_id,
    rayon_km=5.0,
    decalage_jour=0,
    max_zones=24,
):
    """
    Scanne un rayon de `rayon_km` (5 km par défaut) autour de (latitude, longitude)
    pour identifier et cartographier les zones où la probabilité de récolter l'espèce
    `espece_id` est la plus élevée au jour J+`decalage_jour` :
    1. Charge en parallèle :
       - Les séries météo 31j (J-20 à J+10)
       - Le fond pédologique régional SoilGrids
       - Le Modèle Numérique de Terrain (MNT 8x8 = 64 points) sur le rayon de 5 km
       - Tous les polygones forestiers IGN BD Forêt V2 du rayon de 5 km
    2. Échantillonne :
       - Chaque polygone forestier IGN (intérieur + lisière à ~15 m)
       - Une grille spatiale concentrique couvrant tout le disque de 5 km (prairies, clairières, vallons, versants)
    3. Évalue le modèle mycologique complet (biotope, pH local, altitude, pente, exposition Adret/Ubac,
       cinétique et stades de maturité des carpophores) sur chaque zone candidate.
    """
    is_mode_auto = espece_id in (None, "", "auto", "toutes", "all", "top")
    espece = None
    if not is_mode_auto:
        cible_propre = str(espece_id).strip().lower()
        espece = next((e for e in CATALOGUE_ESPECES if (
            e.get("id", "").lower() == cible_propre
            or e.get("nom", "").strip().lower() == cible_propre
            or e.get("nom_scientifique", "").strip().lower() == cible_propre
        )), None)
        if not espece:
            espece = next((e for e in CATALOGUE_ESPECES if (
                e.get("nom", "").lower() in cible_propre
                or cible_propre in e.get("nom", "").lower()
                or e.get("id", "").lower() in cible_propre
                or cible_propre in e.get("nom_scientifique", "").lower()
            )), None)
        if not espece:
            is_mode_auto = True

    with ThreadPoolExecutor(max_workers=4) as pool:
        fut_meteo = pool.submit(recuperer_donnees_meteo, latitude, longitude, 20, 11)
        fut_sol = pool.submit(recuperer_donnees_sol, latitude, longitude)
        fut_mnt = pool.submit(construire_mnt_rayon, latitude, longitude, rayon_km, 8)
        fut_parcelles = pool.submit(recuperer_polygones_foret_rayon, latitude, longitude, rayon_km)

        meteo_ref = fut_meteo.result()
        sol_ref = fut_sol.result()
        mnt = fut_mnt.result()
        parcelles = fut_parcelles.result()

    if not meteo_ref or not meteo_ref.get("time"):
        raise RuntimeError("Impossible de récupérer les données météorologiques pour le scan 5 km.")

    dates = meteo_ref["time"]
    idx_aujourd_hui = 20
    decalage_jour = max(0, min(10, int(decalage_jour)))
    idx_cible = min(len(dates) - 1, idx_aujourd_hui + decalage_jour)
    date_cible = dates[idx_cible]

    topo_centre = calculer_topographie_sur_mnt(mnt, latitude, longitude)
    alt_centre = topo_centre.get("altitude_m") or 250.0

    # Liste des espèces à tester : automatique (top saison) ou espèce ciblée
    if is_mode_auto:
        mois_actuel = datetime.now().month
        especes_a_tester = selectionner_catalogue_contextuel(latitude, longitude, mois_actuel)[:20]
    else:
        especes_a_tester = [espece]

    # --- Génération des zones candidates dans le disque de 5 km ---
    candidats = []
    toutes_especes_rayon = {}

    # A. Échantillonnage des parcelles forestières IGN réelles et de leurs lisières
    for idx_p, p in enumerate(parcelles):
        pt_int = _trouver_point_interieur_polygone(p["poly"], latitude, longitude, rayon_km)
        if pt_int:
            lat_i, lon_i = pt_int
            foret_int = {
                "en_zone_boisee": True,
                "en_lisiere": False,
                "distance_foret_m": 0.0,
                "peuplements": [{
                    "formation_vegetale": p["formation_vegetale"],
                    "essence": p["essence"],
                    "code_tfv": p["code_tfv"],
                    "distance_m": 0.0,
                }],
                "peuplements_lisiere": [],
                "parcelle_principale": p,
            }
            candidats.append((lat_i, lon_i, foret_int, p))

        # Point de lisière (~15 m à l'extérieur d'un sommet de la parcelle)
        ext = p["poly"][0]
        if ext:
            sx, sy = ext[0][0], ext[0][1]
            # Vecteur depuis le barycentre vers le sommet extérieur, prolongé de ~15 m
            if pt_int:
                dy = sy - pt_int[0]
                dx = sx - pt_int[1]
            else:
                dy = sy - latitude
                dx = sx - longitude
            norm_m = math.sqrt((dx * 111320.0 * math.cos(math.radians(sy))) ** 2 + (dy * 111132.0) ** 2)
            if norm_m > 1.0:
                fact_15m = 16.0 / norm_m
                lat_lis = round(sy + dy * fact_15m, 5)
                lon_lis = round(sx + dx * fact_15m, 5)
                dist_km_lis, _, _ = calculer_distance_et_cap(latitude, longitude, lat_lis, lon_lis)
                if dist_km_lis <= rayon_km:
                    qual_lis = qualifier_point_dans_parcelles(lat_lis, lon_lis, parcelles)
                    if not qual_lis["en_zone_boisee"]:
                        if not qual_lis["en_lisiere"]:
                            qual_lis["en_lisiere"] = True
                            qual_lis["distance_foret_m"] = 15.0
                            qual_lis["peuplements_lisiere"] = [{
                                "formation_vegetale": p["formation_vegetale"],
                                "essence": p["essence"],
                                "code_tfv": p["code_tfv"],
                                "distance_m": 15.0,
                            }]
                        candidats.append((lat_lis, lon_lis, qual_lis, None))

    # B. Grille spatiale concentrique sur tout le disque de 5 km (capte prairies, clairières, vallons et versants)
    cos_lat = max(0.2, math.cos(math.radians(latitude)))
    couronnes = [
        (0.0, 1),
        (0.75, 8),
        (1.5, 12),
        (2.3, 16),
        (3.1, 20),
        (3.9, 24),
        (4.7, 28),
    ]
    for r_km, nb_angles in couronnes:
        if r_km > rayon_km:
            continue
        for k in range(nb_angles):
            angle_rad = 2.0 * math.pi * k / nb_angles
            dlat = (r_km * math.cos(angle_rad)) / 111.132
            dlon = (r_km * math.sin(angle_rad)) / (111.320 * cos_lat)
            lat_g = round(latitude + dlat, 5)
            lon_g = round(longitude + dlon, 5)
            qual = qualifier_point_dans_parcelles(lat_g, lon_g, parcelles)
            candidats.append((lat_g, lon_g, qual, qual.get("parcelle_principale") if qual["en_zone_boisee"] else None))

    # --- Évaluation mycologique de chaque candidat ---
    zones_evaluees = []
    for lat_z, lon_z, foret_z, parcelle_poly in candidats:
        dist_km, cap_deg, dir_card = calculer_distance_et_cap(latitude, longitude, lat_z, lon_z)
        if dist_km > rayon_km + 0.05:
            continue

        topo_z = calculer_topographie_sur_mnt(mnt, lat_z, lon_z)
        sol_z = estimer_sol_local_zone(sol_ref, foret_z, topo_z)
        profil_z = {
            "coordonnees": {"latitude": lat_z, "longitude": lon_z},
            "altitude_m": topo_z["altitude_m"],
            "topographie": topo_z,
            "sol": sol_z,
            "foret": foret_z,
        }

        delta_alt = (topo_z["altitude_m"] or alt_centre) - alt_centre
        meteo_z = _adapter_meteo_altitude(meteo_ref, delta_alt)

        meilleur_esp = None
        meilleur_score = -1
        meilleur_bio = 0.0
        meilleure_res = None

        for esp_cand in especes_a_tester:
            score_biotope = evaluer_biotope(esp_cand, profil_z)
            if score_biotope < 0.12:
                continue
            res_cible = calculer_score_jour(
                esp_cand,
                meteo_z,
                idx_cible,
                score_biotope,
                topographie=topo_z,
                profil_env=profil_z,
            )
            sc = res_cible["score_pct"]

            # Enregistrement multi-espèces de toutes les espèces viables dans le rayon de 5 km
            if is_mode_auto and sc >= 15:
                esp_id_cand = esp_cand["id"]
                if esp_id_cand not in toutes_especes_rayon or sc > toutes_especes_rayon[esp_id_cand]["score_max_pct"]:
                    toutes_especes_rayon[esp_id_cand] = {
                        "id": esp_id_cand,
                        "nom": esp_cand["nom"],
                        "nom_scientifique": esp_cand.get("nom_scientifique", ""),
                        "comestibilite": esp_cand.get("comestibilite", "Comestible"),
                        "score_max_pct": sc,
                        "meilleure_distance_km": round(dist_km, 2),
                        "direction": dir_card,
                        "biotope": _formater_libelle_biotope_zone(foret_z),
                        "latitude": lat_z,
                        "longitude": lon_z,
                        "confusion_toxique": obtenir_confusion_toxique(esp_id_cand),
                    }

            if sc > meilleur_score:
                meilleur_score = sc
                meilleur_esp = esp_cand
                meilleur_bio = score_biotope
                meilleure_res = res_cible

        if not meilleur_esp or meilleur_score <= 0:
            continue

        # Calcul rapide du score max sur les 4 jours autour/après la date cible
        score_max_proche = meilleur_score
        meilleure_echeance = "J" if decalage_jour == 0 else f"J+{decalage_jour}"
        for d_alt in range(max(0, decalage_jour), min(11, decalage_jour + 4)):
            if d_alt == decalage_jour:
                continue
            r_alt = calculer_score_jour(
                meilleur_esp,
                meteo_z,
                idx_aujourd_hui + d_alt,
                meilleur_bio,
                topographie=topo_z,
                profil_env=profil_z,
            )
            if r_alt["score_pct"] > score_max_proche:
                score_max_proche = r_alt["score_pct"]
                meilleure_echeance = "J" if d_alt == 0 else f"J+{d_alt}"

        type_milieu = (
            "foret"
            if foret_z.get("en_zone_boisee")
            else ("lisiere" if foret_z.get("en_lisiere") else "prairie")
        )

        zones_evaluees.append({
            "latitude": lat_z,
            "longitude": lon_z,
            "distance_km": round(dist_km, 2),
            "cap_deg": cap_deg,
            "direction_cardinale": dir_card,
            "score": meilleur_score,
            "score_pct": meilleur_score,
            "score_max_proche_pct": score_max_proche,
            "meilleure_echeance": meilleure_echeance,
            "compatibilite_biotope_pct": int(round(meilleur_bio * 100)),
            "type_milieu": type_milieu,
            "nom_espece": meilleur_esp["nom"],
            "libelle_biotope": _formater_libelle_biotope_zone(foret_z),
            "altitude_m": topo_z["altitude_m"],
            "pente_deg": topo_z["pente_deg"],
            "orientation": topo_z["orientation"],
            "ph_estime": sol_z["ph"],
            "type_sol": sol_z["type_sol"],
            "details_jour": meilleure_res["details"],
            "espece": {
                "id": meilleur_esp["id"],
                "nom": meilleur_esp["nom"],
                "nom_scientifique": meilleur_esp.get("nom_scientifique", ""),
                "comestibilite": meilleur_esp.get("comestibilite", "Comestible"),
            },
            "confusion_toxique": obtenir_confusion_toxique(meilleur_esp["id"]),
            "_parcelle": parcelle_poly,
        })

    # Tri décroissant par score au jour cible, puis score max proche, puis biotope, puis proximité
    zones_evaluees.sort(
        key=lambda z: (
            z["score_pct"],
            z["score_max_proche_pct"],
            z["compatibilite_biotope_pct"],
            -z["distance_km"],
        ),
        reverse=True,
    )

    # Dédoublonnage spatial avec diversification d'espèces en mode automatique
    zones_retenues = []

    # En mode auto : sélectionner d'abord la meilleure zone pour chaque espèce détectée
    if is_mode_auto and toutes_especes_rayon:
        especes_deja_placees = set()
        for z in zones_evaluees:
            esp_id_z = z["espece"]["id"]
            if esp_id_z not in especes_deja_placees:
                parcelle = z.pop("_parcelle", None)
                if parcelle and parcelle.get("poly") and parcelle["poly"][0]:
                    z["polygone_coords"] = _simplifier_anneau_leaflet(parcelle["poly"][0], max_points=36)
                else:
                    z["polygone_coords"] = None
                z["rang"] = len(zones_retenues) + 1
                zones_retenues.append(z)
                especes_deja_placees.add(esp_id_z)
                if len(zones_retenues) >= max_zones:
                    break

    # Compléter avec les meilleures zones restantes non encore incluses
    for z in zones_evaluees:
        if len(zones_retenues) >= max_zones:
            break
        deja_prise = any(
            abs(z["latitude"] - r["latitude"]) < 0.0001 and abs(z["longitude"] - r["longitude"]) < 0.0001
            for r in zones_retenues
        )
        if deja_prise:
            continue
        trop_proche = False
        for existante in zones_retenues:
            d_inter, _, _ = calculer_distance_et_cap(
                z["latitude"], z["longitude"], existante["latitude"], existante["longitude"]
            )
            if d_inter < 0.35 and z["type_milieu"] == existante["type_milieu"]:
                trop_proche = True
                break
        if not trop_proche:
            parcelle = z.pop("_parcelle", None)
            if parcelle and parcelle.get("poly") and parcelle["poly"][0]:
                z["polygone_coords"] = _simplifier_anneau_leaflet(parcelle["poly"][0], max_points=36)
            else:
                z["polygone_coords"] = None
            z["rang"] = len(zones_retenues) + 1
            zones_retenues.append(z)

    # Synthèse des meilleurs champignons trouvés dans le rayon de 5 km
    if is_mode_auto and toutes_especes_rayon:
        top_especes_5km = sorted(
            toutes_especes_rayon.values(), key=lambda x: x["score_max_pct"], reverse=True
        )
    else:
        especes_uniques = {}
        for z in zones_retenues:
            z_esp = z.get("espece") or {}
            nom_esp = z_esp.get("nom") or "Champignon"
            if nom_esp not in especes_uniques or z["score_pct"] > especes_uniques[nom_esp]["score_max_pct"]:
                especes_uniques[nom_esp] = {
                    "nom": nom_esp,
                    "nom_scientifique": z_esp.get("nom_scientifique", ""),
                    "comestibilite": z_esp.get("comestibilite", "Comestible"),
                    "score_max_pct": z["score_pct"],
                    "meilleure_distance_km": z["distance_km"],
                    "direction": z["direction_cardinale"],
                    "biotope": z["libelle_biotope"],
                    "latitude": z["latitude"],
                    "longitude": z["longitude"],
                }
        top_especes_5km = sorted(especes_uniques.values(), key=lambda x: x["score_max_pct"], reverse=True)

    info_esp = {
        "id": espece["id"] if espece else "auto",
        "nom": espece["nom"] if espece else "Tous les meilleurs champignons",
        "nom_scientifique": espece["nom_scientifique"] if espece else "Multi-espèces automatiques",
        "essences_hotes": espece.get("essences_hotes", []) if espece else [],
        "ph_optimal": espece.get("ph_optimal", "") if espece else "",
    }

    return {
        "centre": {"latitude": latitude, "longitude": longitude, "altitude_m": alt_centre},
        "rayon_km": rayon_km,
        "date_cible": date_cible,
        "echeance": "J" if decalage_jour == 0 else f"J+{decalage_jour}",
        "decalage_jour": decalage_jour,
        "mode_auto": is_mode_auto,
        "top_especes_5km": top_especes_5km,
        "espece": info_esp,
        "nb_parcelles_ign_analysees": len(parcelles),
        "nb_points_testes": len(zones_evaluees),
        "score_max_rayon_pct": zones_retenues[0]["score_pct"] if zones_retenues else 0,
        "zones_optimales": zones_retenues,
    }


if __name__ == "__main__":
    # Test en Forêt domaniale de Mormal (50.2215, 3.7580)
    lat, lon = 50.2215, 3.7580
    print(f"Simulation bioclimatique complète pour ({lat}, {lon})...\n")
    rapport = simuler_pousse_point_gps(lat, lon)

    env = rapport["environnement"]
    print(f"Date du jour (J) : {rapport['date_simulation']}")
    print(f"Altitude         : {env['altitude_m']} m")
    print(f"Sol              : {env['sol']['type_sol']} (pH {env['sol']['ph']})")
    essences_str = ", ".join(
        f"{p['formation_vegetale']} ({p['essence']})"
        for p in env["foret"]["peuplements"]
    ) or "Hors zone forestière répertoriée"
    print(f"Peuplements IGN  : {essences_str}")
    print(f"\nEspèces comestibles de saison ({len(rapport['especes_probables'])} espèces) :")
    print("-" * 95)

    entetes = ["J"] + [f"J+{k}" for k in range(1, 11)]
    print(f"{'Espèce':<30} | {'Biotope':<7} | " + " ".join(f"{h:>4}" for h in entetes))
    print("-" * 95)

    for esp in rapport["especes_probables"]:
        scores_str = " ".join(
            f"{jour['score_pct']:>3}%" for jour in esp["courbe_J_a_J10"]
        )
        print(f"{esp['nom'][:30]:<30} | {esp['compatibilite_biotope_pct']:>5}%  | {scores_str}")
