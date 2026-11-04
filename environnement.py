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


def calculer_distance_et_cap(lat1, lon1, lat2, lon2):
    """
    Calcule la distance orthodromique (en km), l'azimut (en degrés, 0°=Nord, 90°=Est)
    et la direction cardinale (N, NE, E, SE, S, SO, O, NO) du point 1 vers le point 2.
    """
    dy_m = (lat2 - lat1) * 111132.0
    dx_m = (lon2 - lon1) * 111320.0 * math.cos(math.radians((lat1 + lat2) * 0.5))
    dist_km = math.sqrt(dx_m * dx_m + dy_m * dy_m) / 1000.0
    if dist_km < 0.02:
        return 0.0, 0, "Centre"
    cap_deg = int(round((math.degrees(math.atan2(dx_m, dy_m)) + 360.0) % 360.0)) % 360
    directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    idx = int(((cap_deg + 22.5) % 360.0) // 45)
    return round(dist_km, 2), cap_deg, directions[idx]


def construire_mnt_rayon(lat_centre, lon_centre, rayon_km=5.0, taille_grille=8):
    """
    Construit un Modèle Numérique de Terrain (MNT) régulier (8x8 = 64 points) couvrant
    le disque de `rayon_km` autour de (lat_centre, lon_centre) en une seule requête HTTP
    groupée vers Open-Meteo Elevation.
    """
    marge_km = rayon_km + 0.4
    d_lat = marge_km / 111.132
    cos_lat = max(0.2, math.cos(math.radians(lat_centre)))
    d_lon = marge_km / (111.320 * cos_lat)

    min_lat = lat_centre - d_lat
    max_lat = lat_centre + d_lat
    min_lon = lon_centre - d_lon
    max_lon = lon_centre + d_lon

    lats_grille = [
        min_lat + i * (max_lat - min_lat) / (taille_grille - 1)
        for i in range(taille_grille)
    ]
    lons_grille = [
        min_lon + j * (max_lon - min_lon) / (taille_grille - 1)
        for j in range(taille_grille)
    ]

    lats_req = []
    lons_req = []
    for la in lats_grille:
        for lo in lons_grille:
            lats_req.append(la)
            lons_req.append(lo)

    grille_z = [[250.0 for _ in range(taille_grille)] for _ in range(taille_grille)]
    try:
        lats_str = ",".join(f"{x:.5f}" for x in lats_req)
        lons_str = ",".join(f"{x:.5f}" for x in lons_req)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lats_str}&longitude={lons_str}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            elevs = resp.json().get("elevation", [])
            if len(elevs) == len(lats_req):
                k = 0
                for i in range(taille_grille):
                    for j in range(taille_grille):
                        grille_z[i][j] = float(elevs[k]) if elevs[k] is not None else 250.0
                        k += 1
    except requests.RequestException as e:
        print(f"Avertissement MNT Open-Meteo 5km : {e}")

    return {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
        "taille": taille_grille,
        "grille_z": grille_z,
    }


def _interpoler_z_mnt(mnt, lat, lon):
    """Interpolation bilinéaire de l'altitude sur le MNT régulier."""
    n = mnt["taille"]
    u = (lat - mnt["min_lat"]) / max(1e-9, (mnt["max_lat"] - mnt["min_lat"])) * (n - 1)
    v = (lon - mnt["min_lon"]) / max(1e-9, (mnt["max_lon"] - mnt["min_lon"])) * (n - 1)
    u = max(0.0, min(float(n - 1) - 1e-6, u))
    v = max(0.0, min(float(n - 1) - 1e-6, v))
    i = int(u)
    j = int(v)
    du = u - i
    dv = v - j
    g = mnt["grille_z"]
    z00 = g[i][j]
    z01 = g[i][j + 1]
    z10 = g[i + 1][j]
    z11 = g[i + 1][j + 1]
    return (1 - du) * ((1 - dv) * z00 + dv * z01) + du * ((1 - dv) * z10 + dv * z11)


def calculer_topographie_sur_mnt(mnt, latitude, longitude, pas_m=90.0):
    """
    Calcule l'altitude, la pente, l'azimut, l'orientation (Adret/Ubac) et les modificateurs
    microclimatiques d'un point (latitude, longitude) directement à partir du MNT préchargé.
    """
    d_lat = pas_m / 111320.0
    cos_lat = max(0.2, math.cos(math.radians(latitude)))
    d_lon = pas_m / (111320.0 * cos_lat)

    z_c = _interpoler_z_mnt(mnt, latitude, longitude)
    z_n = _interpoler_z_mnt(mnt, latitude + d_lat, longitude)
    z_s = _interpoler_z_mnt(mnt, latitude - d_lat, longitude)
    z_e = _interpoler_z_mnt(mnt, latitude, longitude + d_lon)
    z_w = _interpoler_z_mnt(mnt, latitude, longitude - d_lon)

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

        intensite_pente = min(1.0, pente_deg / 20.0)
        exposition_solaire = -math.cos(math.radians(azimut_deg - 15.0))
        delta_temp_sol_c = round(1.8 * exposition_solaire * intensite_pente, 2)

        perte_pente = max(0.0, (pente_deg - 12.0) / 40.0) * 0.15
        coeff_retention_humidite = round(
            max(0.75, min(1.18, 1.0 - 0.12 * exposition_solaire * intensite_pente - perte_pente)), 2
        )
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


def _simplifier_anneau_leaflet(anneau, max_points=36):
    """
    Convertit un anneau GeoJSON [[lon, lat], ...] en contour Leaflet [[lat, lon], ...]
    sous-échantillonné à au plus `max_points` sommets pour un rendu fluide.
    """
    if not anneau or len(anneau) < 3:
        return []
    n = len(anneau)
    if n <= max_points:
        return [[round(pt[1], 5), round(pt[0], 5)] for pt in anneau]
    pas = max(1, n // max_points)
    pts = [[round(anneau[i][1], 5), round(anneau[i][0], 5)] for i in range(0, n - 1, pas)]
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def _trouver_point_interieur_polygone(poly, lat_centre, lon_centre, rayon_km):
    """
    Trouve un point représentatif strictement à l'intérieur du polygone `poly`
    et situé à moins de `rayon_km` du centre (lat_centre, lon_centre).
    """
    if not poly or not poly[0]:
        return None
    ext = poly[0]
    # Barycentre des sommets situés dans le rayon (ou de tout l'anneau)
    echelle_x = 111.320 * math.cos(math.radians(lat_centre))
    echelle_y = 111.132
    sommets_dans_rayon = [
        pt for pt in ext
        if ((pt[0] - lon_centre) * echelle_x) ** 2 + ((pt[1] - lat_centre) * echelle_y) ** 2 <= rayon_km ** 2
    ]
    base_pts = sommets_dans_rayon if sommets_dans_rayon else ext
    lon_moy = sum(pt[0] for pt in base_pts) / len(base_pts)
    lat_moy = sum(pt[1] for pt in base_pts) / len(base_pts)

    if _point_dans_polygone(lon_moy, lat_moy, poly):
        dist_km, _, _ = calculer_distance_et_cap(lat_centre, lon_centre, lat_moy, lon_moy)
        if dist_km <= rayon_km:
            return round(lat_moy, 5), round(lon_moy, 5)

    # Sinon, teste des points décalés de 15 m vers l'intérieur depuis plusieurs sommets de l'anneau
    pas = max(1, len(base_pts) // 12)
    for i in range(0, len(base_pts), pas):
        sx, sy = base_pts[i][0], base_pts[i][1]
        for alpha in (0.15, 0.35, 0.5):
            tx = sx + alpha * (lon_moy - sx)
            ty = sy + alpha * (lat_moy - sy)
            if _point_dans_polygone(tx, ty, poly):
                dist_km, _, _ = calculer_distance_et_cap(lat_centre, lon_centre, ty, tx)
                if dist_km <= rayon_km:
                    return round(ty, 5), round(tx, 5)
    return None


def recuperer_polygones_foret_rayon(lat_centre, lon_centre, rayon_km=5.0):
    """
    Récupère en une seule requête WFS tous les polygones forestiers IGN BD Forêt V2
    situés dans un rayon de `rayon_km` autour de (lat_centre, lon_centre), avec leurs
    boîtes englobantes précalculées pour l'indexation spatiale rapide.
    """
    d_lat = rayon_km / 111.132
    cos_lat = max(0.2, math.cos(math.radians(lat_centre)))
    d_lon = rayon_km / (111.320 * cos_lat)

    min_lat = lat_centre - d_lat
    max_lat = lat_centre + d_lat
    min_lon = lon_centre - d_lon
    max_lon = lon_centre + d_lon

    url = (
        "https://data.geopf.fr/wfs/ows"
        "?SERVICE=WFS"
        "&VERSION=2.0.0"
        "&REQUEST=GetFeature"
        "&TYPENAMES=LANDCOVER.FORESTINVENTORY.V2:formation_vegetale"
        "&SRSNAME=CRS:84"
        f"&BBOX={min_lon:.5f},{min_lat:.5f},{max_lon:.5f},{max_lat:.5f},CRS:84"
        "&OUTPUTFORMAT=application/json"
        "&COUNT=350"
    )

    parcelles = []
    try:
        resp = requests.get(url, timeout=14)
        if resp.status_code == 200:
            features = resp.json().get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                if not geom:
                    continue
                tfv = props.get("tfv") or props.get("libelle") or ""
                essence = props.get("essence") or ""
                code_tfv = props.get("code_tfv") or ""
                if not (tfv or essence):
                    continue

                gtype = geom.get("type")
                coords = geom.get("coordinates", [])
                polys = [coords] if gtype == "Polygon" else (coords if gtype == "MultiPolygon" else [])

                for poly in polys:
                    if not poly or not poly[0] or len(poly[0]) < 3:
                        continue
                    ext = poly[0]
                    lons_p = [pt[0] for pt in ext]
                    lats_p = [pt[1] for pt in ext]
                    parcelles.append({
                        "formation_vegetale": tfv,
                        "essence": essence,
                        "code_tfv": code_tfv,
                        "poly": poly,
                        "bbox": (min(lons_p), min(lats_p), max(lons_p), max(lats_p)),
                    })
    except requests.RequestException as e:
        print(f"Avertissement WFS IGN 5km : {e}")

    return parcelles


def qualifier_point_dans_parcelles(lat, lon, parcelles):
    """
    Détermine géométriquement à partir de la liste des `parcelles` IGN chargées en mémoire
    si le point (lat, lon) est en Forêt (<= 5 m), en Lisière (5..25 m) ou en Prairie (> 25 m).
    Utilise un filtrage par boîte englobante (BBOX) pour une exécution ultra-rapide.
    """
    marge_lon = 35.0 / (111320.0 * max(0.2, math.cos(math.radians(lat))))
    marge_lat = 35.0 / 111132.0

    peuplements_int = []
    peuplements_lis = []
    vus_int = set()
    vus_lis = set()
    dist_min = float("inf")
    parcelle_principale = None

    for p in parcelles:
        b_min_lon, b_min_lat, b_max_lon, b_max_lat = p["bbox"]
        if (
            lon < b_min_lon - marge_lon
            or lon > b_max_lon + marge_lon
            or lat < b_min_lat - marge_lat
            or lat > b_max_lat + marge_lat
        ):
            continue

        poly = p["poly"]
        if _point_dans_polygone(lon, lat, poly):
            d = 0.0
        else:
            d = min(_distance_point_anneau_m(lon, lat, anneau) for anneau in poly)

        if d < dist_min:
            dist_min = d
            parcelle_principale = p

        cle = (p["formation_vegetale"], p["essence"], p["code_tfv"])
        if d <= 5.0:
            if cle not in vus_int:
                vus_int.add(cle)
                peuplements_int.append({
                    "formation_vegetale": p["formation_vegetale"],
                    "essence": p["essence"],
                    "code_tfv": p["code_tfv"],
                    "distance_m": round(d, 1),
                })
        elif d <= 25.0:
            if cle not in vus_lis:
                vus_lis.add(cle)
                peuplements_lis.append({
                    "formation_vegetale": p["formation_vegetale"],
                    "essence": p["essence"],
                    "code_tfv": p["code_tfv"],
                    "distance_m": round(d, 1),
                })

    en_zone_boisee = len(peuplements_int) > 0
    en_lisiere = (not en_zone_boisee) and (len(peuplements_lis) > 0)

    return {
        "en_zone_boisee": en_zone_boisee,
        "en_lisiere": en_lisiere,
        "distance_foret_m": round(dist_min, 1) if dist_min < float("inf") else None,
        "peuplements": peuplements_int,
        "peuplements_lisiere": peuplements_lis if en_lisiere else [],
        "parcelle_principale": parcelle_principale,
    }


def estimer_sol_local_zone(sol_reference, foret_zone, topo_zone):
    """
    Adapte localement les propriétés pédologiques (pH, texture, carbone organique)
    d'une zone candidate dans le rayon de 5 km en combinant le fond géologique régional
    (SoilGrids au centre) et l'effet bio-indicateur de l'humus local (conifères/châtaigniers
    acidifiants vs chênaie/hêtraie vs prairie ouverte) ainsi que la pente.
    """
    ph_ref = (sol_reference or {}).get("ph") or 5.8
    argile_ref = (sol_reference or {}).get("argile_pct") or 20.0
    sable_ref = (sol_reference or {}).get("sable_pct") or 35.0
    limon_ref = (sol_reference or {}).get("limon_pct") or 45.0

    peuplements = foret_zone.get("peuplements") or foret_zone.get("peuplements_lisiere") or []
    essences_txt = " ".join(
        f"{p.get('formation_vegetale', '')} {p.get('essence', '')}" for p in peuplements
    ).lower()

    if foret_zone.get("en_zone_boisee"):
        if any(k in essences_txt for k in ("pin", "conifère", "épicéa", "sapin", "mélèze", "lande")):
            ph_bio = 5.1
            sable_bio = max(sable_ref, 48.0)
            argile_bio = min(argile_ref, 18.0)
            soc = 45.0
        elif "châtaignier" in essences_txt:
            ph_bio = 5.25
            sable_bio = max(sable_ref, 40.0)
            argile_bio = min(argile_ref, 20.0)
            soc = 42.0
        elif any(k in essences_txt for k in ("frêne", "charme", "orme", "tilleul")):
            ph_bio = 6.3
            sable_bio = sable_ref
            argile_bio = max(argile_ref, 24.0)
            soc = 38.0
        else:
            # Chêne, Hêtre, Feuillus mélangés
            ph_bio = 5.75
            sable_bio = sable_ref
            argile_bio = argile_ref
            soc = 38.0
        # En sous-bois, l'humus forestier (0-5 cm) impose à 65 % son pH bio-indicateur sur la roche-mère
        ph_local = round(0.35 * ph_ref + 0.65 * ph_bio, 2)
    elif foret_zone.get("en_lisiere"):
        ph_local = round(0.50 * ph_ref + 0.50 * 6.1, 2)
        sable_bio = sable_ref
        argile_bio = argile_ref
        soc = 32.0
    else:
        # Prairie / Milieu ouvert
        ph_local = round(0.45 * ph_ref + 0.55 * 6.4, 2)
        sable_bio = sable_ref
        argile_bio = argile_ref
        soc = 26.0

    # Effet topographique sur la texture : colluvionnement argilo-limoneux en bas de pente plate,
    # érosion plus superficielle/drainante sur pente forte (> 12°)
    pente_deg = (topo_zone or {}).get("pente_deg") or 0.0
    if pente_deg > 12.0:
        sable_local = min(75.0, round(sable_bio + 6.0, 1))
        argile_local = max(8.0, round(argile_bio - 4.0, 1))
    elif pente_deg < 2.5:
        sable_local = max(15.0, round(sable_bio - 3.0, 1))
        argile_local = min(50.0, round(argile_bio + 3.0, 1))
    else:
        sable_local = round(sable_bio, 1)
        argile_local = round(argile_bio, 1)

    limon_local = round(max(5.0, 100.0 - sable_local - argile_local), 1)
    return {
        "ph": ph_local,
        "argile_pct": argile_local,
        "sable_pct": sable_local,
        "limon_pct": limon_local,
        "carbone_organique_g_kg": soc,
        "type_sol": qualifier_sol(ph_local, argile_local, sable_local),
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
