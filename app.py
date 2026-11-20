from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    """
    try:
        return simuler_pousse_point_gps(round(lat, 5), round(lon, 5))
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

    try:
        return rechercher_zones_optimales_5km(
            round(lat, 5),
            round(lon, 5),
            espece_id=target_espece,
            rayon_km=rayon_km,
            decalage_jour=target_jour,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
