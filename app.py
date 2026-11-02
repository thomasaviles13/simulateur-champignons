from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from modele_fructification import CATALOGUE_ESPECES, simuler_pousse_point_gps

app = FastAPI(
    title="Simulateur Bioclimatique et Édaphique de Fructification",
    description="Prédiction de pousse de champignons sauvages comestibles (J à J+10)",
    version="2.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def afficher_interface():
    """Sert l'application web cartographique Leaflet.js."""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/especes")
def lister_catalogue_especes():
    """Renvoie la totalité du catalogue des 42 espèces comestibles."""
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
