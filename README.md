# 🍄 Simulateur Bioclimatique & Édaphique de Pousse de Champignons

📲 **[Télécharger l'application Android (`SimulateurChampignons.apk`)](https://github.com/thomasaviles13/simulateur-champignons/raw/main/SimulateurChampignons.apk)**

Simulateur de fructification mycologique sauvage (42 espèces comestibles) croisant en temps réel :
- **Météorologie sur 31 jours (`J-20` à `J+10`)** : Open-Meteo (températures air/sol, humidité du sol 0–7 cm, ETP FAO, précipitations, vent, rayonnement).
- **Topographie fine** : Altitude, pente (degrés et %), exposition / azimut (Adret vs Ubac) et micro-climat associé.
- **Cartographie forestière IGN BD Forêt® V2** : Détection géométrique exacte (`Point-in-Polygon` + clairières + distance métrique à la lisière) distinguant **Forêt**, **Prairie en lisière forestière (≤ 25 m)** et **Prairie / Milieu ouvert (> 25 m)**.
- **Pédologie** : SoilGrids v2.0 (pH 0–5 cm, argile, sable, limon, carbone organique) avec repli bio-indicateur.
- **Cinétique et stades de maturité des carpophores** : Guildes trophiques (*mycorhiziens*, *saprophytes*, *lignicoles*) et répartition dynamique entre **🌱 En pousse**, **🍄 Adultes** et **🍂 Vieillissants**.

---

## 📁 Structure du dépôt

- `app.py`, `environnement.py`, `meteo.py`, `modele_fructification.py`, `static/index.html` : Application Web FastAPI.
- `android-app/` : Application Android native autonome (Kotlin + Jetpack Compose + carte interactive IGN/OSM).
- `.github/workflows/android-apk.yml` : Compilation automatique de `SimulateurChampignons.apk` sur GitHub Actions à chaque `git push` et publication automatique dans **GitHub Releases** lors d'un tag `v*`.

---

## 🔄 Gestion des versions (Versioning)

Dans [`android-app/app/build.gradle.kts`](android-app/app/build.gradle.kts) :
- `versionCode` : Entier incrémenté à chaque mise à jour Android (`1`, `2`, `3`...) permettant à Android de mettre à jour l'application sans perdre vos données.
- `versionName` : Version sémantique (`"1.0.0"`, `"1.1.0"`, `"1.1.1"`).
