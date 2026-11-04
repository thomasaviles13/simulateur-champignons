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
        "mois_optimaux": [8, 9, 10, 11],
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
        "temp_sol_optimale": (7.0, 15.0),
        "temp_sol_limites": (3.0, 19.0),
        "pluie_20j_optimale_mm": (55.0, 150.0),
        "delai_maturation_jours": (8, 16),
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
        "ph_optimal": (4.8, 7.0),
        "temp_sol_optimale": (6.0, 14.0),
        "temp_sol_limites": (2.0, 18.0),
        "pluie_20j_optimale_mm": (45.0, 120.0),
        "delai_maturation_jours": (8, 15),
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
        "mois_optimaux": [8, 9, 10, 11],
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
        "mois_optimaux": [9, 10, 11],
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
        "mois_optimaux": [9, 10, 11],
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
        "mois_optimaux": [8, 9, 10, 11],
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
        "mois_optimaux": [9, 10, 11],
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
        "delai_maturation_jours": (5, 10),
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
}


def _type_trophique_espece(espece):
    esp_id = espece["id"]
    if esp_id in ESPECES_LIGNICOLES:
        return "lignicole"
    if esp_id in ESPECES_SAPROPHYTES:
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
    if esp_id in ("coprin_chevelu", "rose_des_pres"):
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
    ):
        return 8
    # Cèpes, Bolets, Coulemelles, Amanites, Russules, Lactaires, Tricholomes, Laccaire, Marasme
    return 6


# Espèces cryophiles dont la fructification est stimulée par les premières gelées blanches (-2.5°C à +2°C)
ESPECES_CRYOPHILES_GEL = {
    "pied_bleu",
    "chanterelle_tube",
    "chanterelle_jaunissante",
    "pleurote_huitre",
    "tricholome_terreux",
    "tete_de_moine",
    "pied_de_mouton_roussissant",
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

    pluie_maturation = 0.0
    for idx_p in range(debut_20j, index_jour + 1):
        age_j = index_jour - idx_p
        poids = _poids_pluie_selon_age(age_j)
        if poids > 0.0:
            pluie_maturation += _pluie_efficace_sol(precips[idx_p]) * poids
    pluie_maturation = round(pluie_maturation, 1)

    idx_mat_debut = max(0, index_jour - d_fin)
    idx_mat_fin = max(0, index_jour - d_debut + 1)
    cumul_avant_emergence = round(
        sum(_pluie_efficace_sol(p) for p in precips[debut_20j:idx_mat_fin]), 1
    )

    p_opt_min, p_opt_max = espece["pluie_20j_optimale_mm"]
    score_cumul_20j = _score_intervalle(
        cumul_avant_emergence, p_opt_min * 0.70, p_opt_max, 4.0, p_opt_max + 90.0
    )
    score_maturation = _score_intervalle(
        pluie_maturation, p_opt_min * 0.42, p_opt_max * 0.80, 1.5, p_opt_max * 1.15
    )

    # Stress hydrique antérieur (« Réveil du mycélium » / Effet Birch) vs Asphyxie mycélienne
    pluie_avant_induction = sum(
        _pluie_efficace_sol(p) for p in precips[debut_20j:idx_mat_debut]
    )
    bonus_reveil_mycelien = 1.0
    if pluie_avant_induction < 12.0 and pluie_maturation >= p_opt_min * 0.40:
        # Contraste sec -> humide franc : stimule puissamment la fructification
        bonus_reveil_mycelien = 1.12
    elif params_eco["risque_asphyxie_argile"] and cumul_20j > 135.0:
        # Engorgement hydrique sur sol argileux plat (manque d'oxygène pour le mycélium)
        bonus_reveil_mycelien = 0.72

    score_pluie = min(1.0, (0.42 * score_cumul_20j + 0.58 * score_maturation) * bonus_reveil_mycelien)

    # 5. Phase B : Humidité superficielle du sol (0-7 cm) et hygrométrie de l'air pendant la pousse
    fenetre_hum = [
        h for h in humidites_sol[max(0, index_jour - 2) : index_jour + 1] if h is not None
    ]
    hum_moy = round(sum(fenetre_hum) / len(fenetre_hum), 3) if fenetre_hum else 0.25
    score_humidite_sol = _score_intervalle(hum_moy, 0.22, 0.42, 0.09, 0.55)
    score_humidite = 0.75 * score_humidite_sol + 0.25 * coeff_assechement_air

    # Facteur hydrique global (l'induction préalable est indispensable pour qu'il y ait des primordia)
    score_hydrique = score_pluie * (0.35 + 0.65 * score_humidite) if score_pluie < 0.25 else (
        0.58 * score_pluie + 0.42 * score_humidite
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
    else:
        if tmin_sous_bois <= -3.0:
            facteur_gel = 0.08  # Gel fort létal pour les carpophores de Cèpes, Girolles, Amanites, Coulemelles
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
    facteur_dessiccation = 0.35 + 0.65 * min(1.0, coeff_assechement_air * 1.25)
    facteur_limitant_eau = min(1.0, score_hydrique * 1.45) * facteur_dessiccation
    facteur_limitant_temp = min(1.0, score_temp * 1.45) * min(1.0, facteur_gel)

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


def simuler_pousse_point_gps(latitude, longitude, past_days=20, forecast_days=11):
    """
    Exécute la simulation complète pour un point GPS :
    1. Récupère le profil environnemental (altitude, sol SoilGrids, essences IGN BD Forêt)
    2. Récupère la météo sur J-20 à J+10 (31 jours au total)
    3. Sélectionne toutes les espèces comestibles susceptibles de pousser aux dates J..J+10
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

    # Mois couverts entre J et J+10
    mois_periode = {
        int(dates[i].split("-")[1]) for i in range(idx_aujourd_hui, nb_jours_total)
    }

    resultats_especes = []
    for espece in CATALOGUE_ESPECES:
        # Garde les espèces actives pendant au moins un des mois de la période J..J+10
        if not ( set(espece["mois_actifs"]) & mois_periode ):
            continue

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

        resultats_especes.append({
            "id": espece["id"],
            "nom": espece["nom"],
            "nom_scientifique": espece["nom_scientifique"],
            "compatibilite_biotope_pct": int(round(score_biotope * 100)),
            "score_actuel_J": score_j,
            "score_max_J10": score_max_10j,
            "courbe_J_a_J10": previsions_11j,
        })

    # Tri par score maximum sur la période J..J+10 décroissant
    resultats_especes.sort(
        key=lambda e: (e["score_max_J10"], e["score_actuel_J"]), reverse=True
    )

    profil_env["microclimat_canopee_sol"] = _extraire_parametres_edaphiques_et_canopee(profil_env)

    return {
        "date_simulation": dates[idx_aujourd_hui],
        "environnement": profil_env,
        "meteo_periode": {
            "dates": dates,
            "index_aujourd_hui": idx_aujourd_hui,
            "precipitation_sum": meteo.get("precipitation_sum", []),
            "soil_temperature_0cm": meteo.get("soil_temperature_0cm", []),
            "soil_moisture_0_to_7cm": meteo.get("soil_moisture_0_to_7cm", []),
            "temperature_2m_min": meteo.get("temperature_2m_min", []),
            "wind_speed_10m_max": meteo.get("wind_speed_10m_max", []),
            "et0_fao_evapotranspiration": meteo.get("et0_fao_evapotranspiration", []),
            "relative_humidity_2m": meteo.get("relative_humidity_2m", []),
        },
        "especes_probables": resultats_especes,
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
    espece = next((e for e in CATALOGUE_ESPECES if e["id"] == espece_id), None)
    if not espece:
        raise ValueError(f"Espèce inconnue : {espece_id}")

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

    # --- Génération des zones candidates dans le disque de 5 km ---
    candidats = []

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

        score_biotope = evaluer_biotope(espece, profil_z)
        delta_alt = (topo_z["altitude_m"] or alt_centre) - alt_centre
        meteo_z = _adapter_meteo_altitude(meteo_ref, delta_alt)

        res_cible = calculer_score_jour(
            espece,
            meteo_z,
            idx_cible,
            score_biotope,
            topographie=topo_z,
            profil_env=profil_z,
        )

        # Calcul rapide du score max sur les 4 jours autour/après la date cible
        score_max_proche = res_cible["score_pct"]
        meilleure_echeance = "J" if decalage_jour == 0 else f"J+{decalage_jour}"
        for d_alt in range(max(0, decalage_jour), min(11, decalage_jour + 4)):
            if d_alt == decalage_jour:
                continue
            r_alt = calculer_score_jour(
                espece,
                meteo_z,
                idx_aujourd_hui + d_alt,
                score_biotope,
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
            "distance_km": dist_km,
            "cap_deg": cap_deg,
            "direction_cardinale": dir_card,
            "score_pct": res_cible["score_pct"],
            "score_max_proche_pct": score_max_proche,
            "meilleure_echeance": meilleure_echeance,
            "compatibilite_biotope_pct": int(round(score_biotope * 100)),
            "type_milieu": type_milieu,
            "libelle_biotope": _formater_libelle_biotope_zone(foret_z),
            "altitude_m": topo_z["altitude_m"],
            "pente_deg": topo_z["pente_deg"],
            "orientation": topo_z["orientation"],
            "ph_estime": sol_z["ph"],
            "type_sol": sol_z["type_sol"],
            "details_jour": res_cible["details"],
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

    # Dédoublonnage spatial : évite d'empiler 2 marqueurs à moins de 350 m l'un de l'autre
    zones_retenues = []
    for z in zones_evaluees:
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
            if len(zones_retenues) >= max_zones:
                break

    return {
        "centre": {"latitude": latitude, "longitude": longitude, "altitude_m": alt_centre},
        "rayon_km": rayon_km,
        "date_cible": date_cible,
        "echeance": "J" if decalage_jour == 0 else f"J+{decalage_jour}",
        "decalage_jour": decalage_jour,
        "espece": {
            "id": espece["id"],
            "nom": espece["nom"],
            "nom_scientifique": espece["nom_scientifique"],
            "essences_hotes": espece["essences_hotes"],
            "ph_optimal": espece["ph_optimal"],
        },
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
