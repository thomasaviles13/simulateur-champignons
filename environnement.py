import math
import requests


def recuperer_altitude(latitude, longitude):
    """
    Récupère l'altitude (en mètres) d'un point GPS via l'API Open-Meteo Elevation
    (avec repli sur l'API Altimétrie IGN Géoplateforme si besoin).
    """
    topo = recuperer_topographie(latitude, longitude)
    return topo.get("altitude_m")


def recuperer_topographie(latitude, longitude, pas_m=90.0):
    """
    Calcule l'altitude, la pente (en degrés et %) et l'orientation/exposition du versant
    (Adret Sud vs Ubac Nord) en échantillonnant 5 points en croix autour de (latitude, longitude).
    """
    # Conversion d'un pas en mètres vers des degrés de latitude et longitude
    d_lat = pas_m / 111320.0
    cos_lat = max(0.2, math.cos(math.radians(latitude)))
    d_lon = pas_m / (111320.0 * cos_lat)

    # 5 points : Centre, Nord, Sud, Est, Ouest
    lats = [latitude, latitude + d_lat, latitude - d_lat, latitude, latitude]
    lons = [longitude, longitude, longitude, longitude + d_lon, longitude - d_lon]

    elevations = None
    try:
        lats_str = ",".join(f"{x:.6f}" for x in lats)
        lons_str = ",".join(f"{x:.6f}" for x in lons)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lats_str}&longitude={lons_str}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            elevs = response.json().get("elevation", [])
            if len(elevs) == 5 and all(e is not None for e in elevs):
                elevations = elevs
    except requests.RequestException as e:
        print(f"Avertissement Open-Meteo Elevation : {e}")

    # Repli sur IGN Géoplateforme Altimétrie si besoin
    if elevations is None:
        try:
            lats_str = "|".join(f"{x:.6f}" for x in lats)
            lons_str = "|".join(f"{x:.6f}" for x in lons)
            url_ign = (
                "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json"
                f"?lon={lons_str}&lat={lats_str}&resource=ign_rge_alti_wld&delimiter=|"
            )
            response = requests.get(url_ign, timeout=10)
            if response.status_code == 200:
                items = response.json().get("elevations", [])
                if len(items) == 5:
                    elevations = [it.get("z", 0.0) for it in items]
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de l'altitude IGN : {e}")

    if not elevations:
        return {
            "altitude_m": None,
            "pente_deg": 0.0,
            "pente_pct": 0.0,
            "azimut_deg": None,
            "orientation": "Indéterminée",
            "delta_temp_sol_c": 0.0,
            "coeff_retention_humidite": 1.0,
            "coeff_infiltration_pluie": 1.0,
        }

    z_c, z_n, z_s, z_e, z_w = elevations
    # Gradients dz/dx (Ouest -> Est) et dz/dy (Sud -> Nord)
    dz_dx = (z_e - z_w) / (2.0 * pas_m)
    dz_dy = (z_n - z_s) / (2.0 * pas_m)

    pente_rad = math.atan(math.sqrt(dz_dx ** 2 + dz_dy ** 2))
    pente_deg = round(math.degrees(pente_rad), 1)
    pente_pct = round(math.tan(pente_rad) * 100.0, 1)

    if pente_deg < 1.5:
        azimut_deg = None
        orientation = "Terrain plat"
        delta_temp_sol_c = 0.0
        coeff_retention_humidite = 1.0
        coeff_infiltration_pluie = 1.0
    else:
        # Direction de la ligne de plus grande pente vers le bas (-dz_dx, -dz_dy)
        # En azimut géographique : 0° = Nord, 90° = Est, 180° = Sud, 270° = Ouest
        azimut_rad = math.atan2(-dz_dx, -dz_dy)
        azimut_deg = round((math.degrees(azimut_rad) + 360.0) % 360.0, 0)

        secteurs = [
            "Nord (Ubac frais)",
            "Nord-Est (Ubac frais)",
            "Est (Frais matinal)",
            "Sud-Est (Ensoleillé)",
            "Sud (Adret chaud)",
            "Sud-Ouest (Adret chaud)",
            "Ouest (Tempéré)",
            "Nord-Ouest (Frais)",
        ]
        idx_secteur = int(((azimut_deg + 22.5) % 360.0) // 45)
        orientation = secteurs[idx_secteur]

        # Effet thermique de l'exposition : maximal plein Sud-Sud-Ouest (azimut ~195°), minimal plein Nord-Nord-Est (~15°)
        intensite_pente = min(1.0, pente_deg / 20.0)
        exposition_solaire = -math.cos(math.radians(azimut_deg - 15.0))  # +1 au S/SO (195°), -1 au N/NE (15°)
        delta_temp_sol_c = round(1.8 * exposition_solaire * intensite_pente, 2)

        # Rétention d'humidité : accrue à l'Ubac (Nord/Est), réduite à l'Adret (Sud/Sud-Ouest) et sur forte pente
        perte_pente = max(0.0, (pente_deg - 12.0) / 40.0) * 0.15
        coeff_retention_humidite = round(
            max(0.75, min(1.18, 1.0 - 0.12 * exposition_solaire * intensite_pente - perte_pente)), 2
        )

        # Infiltration de la pluie (ruissellement accru au-delà de 15° de pente)
        if pente_deg <= 15.0:
            coeff_infiltration_pluie = 1.0
        else:
            coeff_infiltration_pluie = round(max(0.55, 1.0 - (pente_deg - 15.0) * 0.015), 2)

    return {
        "altitude_m": round(z_c, 1),
        "pente_deg": pente_deg,
        "pente_pct": pente_pct,
        "azimut_deg": int(azimut_deg) if azimut_deg is not None else None,
        "orientation": orientation,
        "delta_temp_sol_c": delta_temp_sol_c,
        "coeff_retention_humidite": coeff_retention_humidite,
        "coeff_infiltration_pluie": coeff_infiltration_pluie,
    }


def _interroger_wms_isric(latitude, longitude, prop, layer_name):
    """
    Interroge directement le serveur MapServer d'ISRIC (WMS GetFeatureInfo)
    qui reste souvent actif même quand l'API REST SoilGrids renvoie une erreur 503.
    """
    delta = 0.001
    bbox = f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta}"
    url = (
        f"https://maps.isric.org/mapserv?map=/map/{prop}.map"
        "&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo"
        f"&LAYERS={layer_name}&QUERY_LAYERS={layer_name}"
        f"&SRS=EPSG:4326&BBOX={bbox}&WIDTH=10&HEIGHT=10&X=5&Y=5"
        "&INFO_FORMAT=application/geojson"
    )
    resp = requests.get(url, timeout=8)
    if resp.status_code == 200:
        features = resp.json().get("features", [])
        if features:
            props = features[0].get("properties", {})
            val = props.get("GRAY_INDEX") or props.get("value_0")
            if val is not None and val > 0:
                return val
    return None


def recuperer_donnees_sol(latitude, longitude, essences_foret=None):
    """
    Interroge l'API SoilGrids (ISRIC) pour récupérer le pH (phh2o) et la texture du sol
    (argile/clay, sable/sand, limon/silt, carbone organique/soc) entre 0 et 5 cm de profondeur.
    Bascule automatiquement sur le serveur WMS ISRIC puis sur une estimation bio-indicatrice
    si le service REST SoilGrids renvoie une erreur 503.
    """
    url = (
        "https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lat={latitude}&lon={longitude}"
        "&property=phh2o&property=clay&property=sand&property=silt&property=soc"
        "&depth=0-5cm&value=mean"
    )
    resultats = {
        "ph": None,
        "argile_pct": None,
        "sable_pct": None,
        "limon_pct": None,
        "carbone_organique_g_kg": None,
        "type_sol": "Inconnu",
        "source": "SoilGrids v2.0 (REST)",
    }

    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            layers = data.get("properties", {}).get("layers", [])
            for layer in layers:
                nom = layer.get("name")
                depths = layer.get("depths", [])
                if not depths:
                    continue
                val = depths[0].get("values", {}).get("mean")
                if val is None:
                    continue
                if nom == "phh2o":
                    resultats["ph"] = round(val / 10.0, 2)
                elif nom == "clay":
                    resultats["argile_pct"] = round(val / 10.0, 1)
                elif nom == "sand":
                    resultats["sable_pct"] = round(val / 10.0, 1)
                elif nom == "silt":
                    resultats["limon_pct"] = round(val / 10.0, 1)
                elif nom == "soc":
                    resultats["carbone_organique_g_kg"] = round(val / 10.0, 1)

            if resultats["ph"] is not None:
                resultats["type_sol"] = qualifier_sol(
                    resultats["ph"], resultats["argile_pct"], resultats["sable_pct"]
                )
                return resultats
    except requests.RequestException:
        pass

    # Repli 1 : Serveur cartographique WMS ISRIC SoilGrids
    try:
        mapping_wms = {
            "phh2o": ("ph", "phh2o_0-5cm_mean", 10.0, 2),
            "clay": ("argile_pct", "clay_0-5cm_mean", 10.0, 1),
            "sand": ("sable_pct", "sand_0-5cm_mean", 10.0, 1),
            "silt": ("limon_pct", "silt_0-5cm_mean", 10.0, 1),
            "soc": ("carbone_organique_g_kg", "soc_0-5cm_mean", 10.0, 1),
        }
        for prop, (cle, layer_name, diviseur, decimales) in mapping_wms.items():
            val = _interroger_wms_isric(latitude, longitude, prop, layer_name)
            if val is not None:
                resultats[cle] = round(val / diviseur, decimales)

        if resultats["ph"] is not None:
            resultats["source"] = "SoilGrids v2.0 (WMS ISRIC)"
            resultats["type_sol"] = qualifier_sol(
                resultats["ph"], resultats["argile_pct"], resultats["sable_pct"]
            )
            return resultats
    except requests.RequestException:
        pass

    # Repli 2 : Estimation pédologique par bio-indication forestière si ISRIC est hors-ligne
    essences_txt = " ".join(essences_foret or []).lower()
    if any(k in essences_txt for k in ("pin", "conifère", "épicéa", "sapin", "lande")):
        resultats.update({"ph": 5.1, "argile_pct": 15.0, "sable_pct": 58.0, "limon_pct": 27.0, "carbone_organique_g_kg": 45.0})
    elif "châtaignier" in essences_txt:
        # Le châtaignier est une essence strictement calcifuge (sols siliceux acides)
        resultats.update({"ph": 5.2, "argile_pct": 18.0, "sable_pct": 42.0, "limon_pct": 40.0, "carbone_organique_g_kg": 42.0})
    elif any(k in essences_txt for k in ("hêtre", "chêne", "feuillus")):
        resultats.update({"ph": 5.8, "argile_pct": 22.0, "sable_pct": 33.0, "limon_pct": 45.0, "carbone_organique_g_kg": 38.0})
    else:
        resultats.update({"ph": 6.5, "argile_pct": 20.0, "sable_pct": 35.0, "limon_pct": 45.0, "carbone_organique_g_kg": 25.0})

    resultats["source"] = "Estimation bio-indicatrice (SoilGrids indisponible)"
    resultats["type_sol"] = qualifier_sol(
        resultats["ph"], resultats["argile_pct"], resultats["sable_pct"]
    )
    return resultats


def qualifier_sol(ph, argile_pct, sable_pct):
    """
    Détermine un qualificatif lisible du sol à partir du pH et de la texture.
    """
    parties = []
    if sable_pct is not None and argile_pct is not None:
        if sable_pct > 60:
            parties.append("Sableux (drainant)")
        elif argile_pct > 35:
            parties.append("Argileux (lourd)")
        else:
            parties.append("Limono-argilo-sableux (équilibré)")

    if ph is not None:
        if ph < 5.5:
            parties.append("fortement acide (siliceux)")
        elif ph < 6.5:
            parties.append("légèrement acide")
        elif ph <= 7.3:
            parties.append("neutre")
        else:
            parties.append("calcaire (basique)")

    return ", ".join(parties) if parties else "Indéterminé"


def _point_dans_anneau(lon, lat, anneau):
    """
    Algorithme Ray-Casting : vérifie si le point (lon, lat) est à l'intérieur d'un anneau [ [lon, lat], ... ].
    """
    dedans = False
    n = len(anneau)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = anneau[i][0], anneau[i][1]
        xj, yj = anneau[j][0], anneau[j][1]
        intersection = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersection:
            dedans = not dedans
        j = i
    return dedans


def _point_dans_polygone(lon, lat, coords_polygone):
    """
    Vérifie si (lon, lat) est dans l'anneau extérieur coords_polygone[0]
    ET n'est PAS dans un trou intérieur coords_polygone[1:] (ex: clairière / prairie enclavée).
    """
    if not coords_polygone or not _point_dans_anneau(lon, lat, coords_polygone[0]):
        return False
    for trou in coords_polygone[1:]:
        if _point_dans_anneau(lon, lat, trou):
            return False
    return True


def _distance_point_anneau_m(lon, lat, anneau):
    """
    Calcule la distance minimale en mètres entre (lon, lat) et les segments d'un anneau.
    """
    if not anneau:
        return float("inf")
    echelle_x = 111320.0 * math.cos(math.radians(lat))
    echelle_y = 111132.0
    dist_min_sq = float("inf")

    for i in range(len(anneau) - 1):
        x1 = (anneau[i][0] - lon) * echelle_x
        y1 = (anneau[i][1] - lat) * echelle_y
        x2 = (anneau[i + 1][0] - lon) * echelle_x
        y2 = (anneau[i + 1][1] - lat) * echelle_y
        dx = x2 - x1
        dy = y2 - y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq <= 1e-9:
            d_sq = x1 * x1 + y1 * y1
        else:
            t = max(0.0, min(1.0, -(x1 * dx + y1 * dy) / seg_len_sq))
            px = x1 + t * dx
            py = y1 + t * dy
            d_sq = px * px + py * py
        if d_sq < dist_min_sq:
            dist_min_sq = d_sq

    return math.sqrt(dist_min_sq)


def _distance_point_geometrie_m(lon, lat, geometrie):
    """
    Renvoie 0.0 si (lon, lat) est strictement à l'intérieur du polygone forestier (hors clairières/trous),
    ou la distance minimale en mètres jusqu'à la lisière du polygone s'il est à l'extérieur.
    """
    if not geometrie:
        return float("inf")
    gtype = geometrie.get("type")
    coords = geometrie.get("coordinates", [])

    polygones = []
    if gtype == "Polygon":
        polygones = [coords]
    elif gtype == "MultiPolygon":
        polygones = coords
    else:
        return float("inf")

    dist_min = float("inf")
    for poly in polygones:
        if _point_dans_polygone(lon, lat, poly):
            return 0.0
        for anneau in poly:
            d = _distance_point_anneau_m(lon, lat, anneau)
            if d < dist_min:
                dist_min = d
    return dist_min


def recuperer_foret_ign(latitude, longitude, rayon_deg=0.001):
    """
    Interroge le service WFS de la Géoplateforme IGN (BD Forêt V2)
    et vérifie géométriquement (Point-in-Polygon + détection des clairières/trous) :
    - Si le point GPS est strictement DANS un polygone forestier (distance <= 5 m) -> Forêt,
    - S'il est en lisière immédiate (5 m < distance <= 25 m) -> Prairie de lisière,
    - S'il est à plus de 25 m de tout boisement -> Prairie / Milieu ouvert (Hors forêt).
    """
    min_lat = latitude - rayon_deg
    max_lat = latitude + rayon_deg
    min_lon = longitude - rayon_deg
    max_lon = longitude + rayon_deg

    # En WFS 2.0.0 avec CRS:84, l'ordre BBOX est min_lon,min_lat,max_lon,max_lat
    url = (
        "https://data.geopf.fr/wfs/ows"
        "?SERVICE=WFS"
        "&VERSION=2.0.0"
        "&REQUEST=GetFeature"
        "&TYPENAMES=LANDCOVER.FORESTINVENTORY.V2:formation_vegetale"
        "&SRSNAME=CRS:84"
        f"&BBOX={min_lon},{min_lat},{max_lon},{max_lat},CRS:84"
        "&OUTPUTFORMAT=application/json"
        "&COUNT=15"
    )

    try:
        response = requests.get(url, timeout=12)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            peuplements_interieur = []
            peuplements_lisiere = []
            vus_int = set()
            vus_lis = set()
            dist_plus_proche = float("inf")

            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                tfv = props.get("tfv") or props.get("libelle")
                essence = props.get("essence")
                code_tfv = props.get("code_tfv")
                if not (tfv or essence):
                    continue

                dist_m = _distance_point_geometrie_m(longitude, latitude, geom)
                if dist_m < dist_plus_proche:
                    dist_plus_proche = dist_m

                cle = (tfv, essence, code_tfv)
                if dist_m <= 5.0:
                    if cle not in vus_int:
                        vus_int.add(cle)
                        peuplements_interieur.append({
                            "formation_vegetale": tfv,
                            "essence": essence,
                            "code_tfv": code_tfv,
                            "distance_m": round(dist_m, 1),
                        })
                elif dist_m <= 25.0:
                    if cle not in vus_lis:
                        vus_lis.add(cle)
                        peuplements_lisiere.append({
                            "formation_vegetale": tfv,
                            "essence": essence,
                            "code_tfv": code_tfv,
                            "distance_m": round(dist_m, 1),
                        })

            en_zone_boisee = len(peuplements_interieur) > 0
            en_lisiere = (not en_zone_boisee) and (len(peuplements_lisiere) > 0)

            return {
                "en_zone_boisee": en_zone_boisee,
                "en_lisiere": en_lisiere,
                "distance_foret_m": round(dist_plus_proche, 1) if dist_plus_proche < float("inf") else None,
                "peuplements": peuplements_interieur,
                "peuplements_lisiere": peuplements_lisiere if en_lisiere else [],
            }
        else:
            print(f"Erreur WFS IGN BD Forêt : {response.status_code}")
    except requests.RequestException as e:
        print(f"Erreur lors de l'interrogation IGN BD Forêt : {e}")

    return {
        "en_zone_boisee": False,
        "en_lisiere": False,
        "distance_foret_m": None,
        "peuplements": [],
        "peuplements_lisiere": [],
    }


def recuperer_profil_environnemental(latitude, longitude):
    """
    Agrège la topographie (altitude, pente, exposition), les peuplements forestiers (IGN BD Forêt)
    et les données pédologiques (SoilGrids).
    """
    topographie = recuperer_topographie(latitude, longitude)
    foret = recuperer_foret_ign(latitude, longitude)
    essences_noms = [
        f"{p.get('formation_vegetale', '')} {p.get('essence', '')}"
        for p in foret.get("peuplements", [])
    ]
    sol = recuperer_donnees_sol(latitude, longitude, essences_foret=essences_noms)

    return {
        "coordonnees": {"latitude": latitude, "longitude": longitude},
        "altitude_m": topographie.get("altitude_m"),
        "topographie": topographie,
        "sol": sol,
        "foret": foret,
    }


if __name__ == "__main__":
    # Coordonnées GPS de test : Forêt de Mormal (Nord) ou Forêt de Fontainebleau
    lat, lon = 50.2215, 3.7580  # Forêt domaniale de Mormal
    print(f"Analyse environnementale pour ({lat}, {lon})...\n")

    profil = recuperer_profil_environnemental(lat, lon)
    print(f"Altitude : {profil['altitude_m']} m")
    print(f"Sol      : {profil['sol']}")
    print(f"Forêt    : {profil['foret']}")
