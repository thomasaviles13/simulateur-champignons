package fr.geekage.champignons.data

import fr.geekage.champignons.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import kotlin.math.*

object ApiEnvironnementMeteo {

    private val cacheMeteo = mutableMapOf<String, SerieMeteo>()

    private fun httpGet(urlStr: String, timeoutMs: Int = 10000): String? {
        var conn: HttpURLConnection? = null
        return try {
            val url = URL(urlStr)
            conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = timeoutMs
                readTimeout = timeoutMs
                setRequestProperty("Accept", "application/json")
                setRequestProperty("User-Agent", "SimulateurChampignonsAndroid/1.0")
            }
            if (conn.responseCode == 200) {
                conn.inputStream.bufferedReader().use { it.readText() }
            } else {
                null
            }
        } catch (e: Exception) {
            null
        } finally {
            conn?.disconnect()
        }
    }

    fun recupererTopographie(latitude: Double, longitude: Double, pasM: Double = 90.0): ProfilTopographique {
        val dLat = pasM / 111320.0
        val cosLat = max(0.2, cos(Math.toRadians(latitude)))
        val dLon = pasM / (111320.0 * cosLat)

        val lats = listOf(latitude, latitude + dLat, latitude - dLat, latitude, latitude)
        val lons = listOf(longitude, longitude, longitude, longitude + dLon, longitude - dLon)

        var elevations: List<Double>? = null
        val latsStr = lats.joinToString(",") { String.format(Locale.US, "%.6f", it) }
        val lonsStr = lons.joinToString(",") { String.format(Locale.US, "%.6f", it) }

        val respOm = httpGet("https://api.open-meteo.com/v1/elevation?latitude=$latsStr&longitude=$lonsStr", 8000)
        if (respOm != null) {
            try {
                val arr = JSONObject(respOm).optJSONArray("elevation")
                if (arr != null && arr.length() == 5) {
                    elevations = (0 until 5).map { arr.optDouble(it, 250.0) }
                }
            } catch (_: Exception) {}
        }

        if (elevations == null) {
            val latsIgn = lats.joinToString("|") { String.format(Locale.US, "%.6f", it) }
            val lonsIgn = lons.joinToString("|") { String.format(Locale.US, "%.6f", it) }
            val respIgn = httpGet(
                "https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json?lon=$lonsIgn&lat=$latsIgn&resource=ign_rge_alti_wld&delimiter=|",
                8000
            )
            if (respIgn != null) {
                try {
                    val arr = JSONObject(respIgn).optJSONArray("elevations")
                    if (arr != null && arr.length() == 5) {
                        elevations = (0 until 5).map { arr.getJSONObject(it).optDouble("z", 250.0) }
                    }
                } catch (_: Exception) {}
            }
        }

        if (elevations == null) {
            return ProfilTopographique(300.0, 2.0, 3.5, null, "Terrain plat", 0.0, 1.0, 1.0)
        }

        val zC = elevations[0]
        val zN = elevations[1]
        val zS = elevations[2]
        val zE = elevations[3]
        val zW = elevations[4]

        val dzDy = (zN - zS) / (2.0 * pasM)
        val dzDx = (zE - zW) / (2.0 * pasM)
        val gradient = hypot(dzDx, dzDy)
        val penteDeg = Math.toDegrees(atan(gradient))
        val pentePct = gradient * 100.0

        if (penteDeg < 1.8) {
            return ProfilTopographique(round1(zC), round1(penteDeg), round1(pentePct), null, "Terrain plat", 0.0, 1.0, 1.0)
        }

        val azimutDeg = (Math.toDegrees(atan2(-dzDx, -dzDy)) + 360.0) % 360.0
        val azimutRad = Math.toRadians(azimutDeg)
        val facteurSud = -cos(azimutRad)
        val intensitePente = min(1.0, penteDeg / 20.0)

        val deltaTempSolC = round2(facteurSud * intensitePente * 1.8)
        val coeffRetHum = round2(max(0.72, min(1.18, 1.0 - (facteurSud * 0.12 * intensitePente) - max(0.0, (penteDeg - 12.0) * 0.01))))
        val coeffInfilt = if (penteDeg <= 10.0) 1.0 else round2(max(0.55, 1.0 - (penteDeg - 10.0) * 0.015))

        val orientation = when {
            azimutDeg >= 337.5 || azimutDeg < 22.5 -> "Nord (Ubac frais)"
            azimutDeg < 67.5 -> "Nord-Est (frais)"
            azimutDeg < 112.5 -> "Est (matinal)"
            azimutDeg < 157.5 -> "Sud-Est (Adret doux)"
            azimutDeg < 202.5 -> "Sud (Adret chaud)"
            azimutDeg < 247.5 -> "Sud-Ouest (Adret chaud)"
            azimutDeg < 292.5 -> "Ouest (humide)"
            else -> "Nord-Ouest (Ubac frais)"
        }

        return ProfilTopographique(
            altitudeM = round1(zC),
            penteDeg = round1(penteDeg),
            pentePct = round1(pentePct),
            azimutDeg = round1(azimutDeg),
            orientation = orientation,
            deltaTempSolC = deltaTempSolC,
            coeffRetentionHumidite = coeffRetHum,
            coeffInfiltrationPluie = coeffInfilt
        )
    }

    private fun pointDansAnneau(lon: Double, lat: Double, anneau: JSONArray): Boolean {
        val n = anneau.length()
        if (n < 3) return false
        var dedans = false
        var j = n - 1
        for (i in 0 until n) {
            val pi = anneau.getJSONArray(i)
            val pj = anneau.getJSONArray(j)
            val xi = pi.optDouble(0)
            val yi = pi.optDouble(1)
            val xj = pj.optDouble(0)
            val yj = pj.optDouble(1)
            val intersecte = ((yi > lat) != (yj > lat)) &&
                (lon < (xj - xi) * (lat - yi) / ((yj - yi).takeIf { abs(it) > 1e-12 } ?: 1e-12) + xi)
            if (intersecte) dedans = !dedans
            j = i
        }
        return dedans
    }

    private fun pointDansPolygone(lon: Double, lat: Double, coordsPoly: JSONArray): Boolean {
        if (coordsPoly.length() == 0) return false
        if (!pointDansAnneau(lon, lat, coordsPoly.getJSONArray(0))) return false
        for (k in 1 until coordsPoly.length()) {
            if (pointDansAnneau(lon, lat, coordsPoly.getJSONArray(k))) return false
        }
        return true
    }

    private fun distancePointAnneauM(lon: Double, lat: Double, anneau: JSONArray): Double {
        val n = anneau.length()
        if (n < 2) return Double.POSITIVE_INFINITY
        val echelleX = 111320.0 * cos(Math.toRadians(lat))
        val echelleY = 111132.0
        var distMinSq = Double.POSITIVE_INFINITY

        for (i in 0 until n - 1) {
            val p1 = anneau.getJSONArray(i)
            val p2 = anneau.getJSONArray(i + 1)
            val x1 = (p1.optDouble(0) - lon) * echelleX
            val y1 = (p1.optDouble(1) - lat) * echelleY
            val x2 = (p2.optDouble(0) - lon) * echelleX
            val y2 = (p2.optDouble(1) - lat) * echelleY
            val dx = x2 - x1
            val dy = y2 - y1
            val segLenSq = dx * dx + dy * dy
            val dSq = if (segLenSq <= 1e-9) {
                x1 * x1 + y1 * y1
            } else {
                val t = (-(x1 * dx + y1 * dy) / segLenSq).coerceIn(0.0, 1.0)
                val px = x1 + t * dx
                val py = y1 + t * dy
                px * px + py * py
            }
            if (dSq < distMinSq) distMinSq = dSq
        }
        return sqrt(distMinSq)
    }

    private fun distancePointGeometrieM(lon: Double, lat: Double, geom: JSONObject?): Double {
        if (geom == null) return Double.POSITIVE_INFINITY
        val gtype = geom.optString("type")
        val coords = geom.optJSONArray("coordinates") ?: return Double.POSITIVE_INFINITY

        val polygones = mutableListOf<JSONArray>()
        if (gtype == "Polygon") {
            polygones.add(coords)
        } else if (gtype == "MultiPolygon") {
            for (i in 0 until coords.length()) {
                polygones.add(coords.getJSONArray(i))
            }
        }

        var distMin = Double.POSITIVE_INFINITY
        for (poly in polygones) {
            if (pointDansPolygone(lon, lat, poly)) return 0.0
            for (k in 0 until poly.length()) {
                val d = distancePointAnneauM(lon, lat, poly.getJSONArray(k))
                if (d < distMin) distMin = d
            }
        }
        return distMin
    }

    fun recupererForetIgn(latitude: Double, longitude: Double, rayonDeg: Double = 0.001): ProfilForet {
        val minLat = String.format(Locale.US, "%.6f", latitude - rayonDeg)
        val maxLat = String.format(Locale.US, "%.6f", latitude + rayonDeg)
        val minLon = String.format(Locale.US, "%.6f", longitude - rayonDeg)
        val maxLon = String.format(Locale.US, "%.6f", longitude + rayonDeg)

        val url = "https://data.geopf.fr/wfs/ows?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature" +
            "&TYPENAMES=LANDCOVER.FORESTINVENTORY.V2:formation_vegetale&SRSNAME=CRS:84" +
            "&BBOX=$minLon,$minLat,$maxLon,$maxLat,CRS:84&OUTPUTFORMAT=application/json&COUNT=15"

        val resp = httpGet(url, 10000) ?: return ProfilForet(false, false, null, emptyList())
        return try {
            val features = JSONObject(resp).optJSONArray("features") ?: JSONArray()
            val interieur = mutableListOf<PeuplementForestier>()
            val lisiere = mutableListOf<PeuplementForestier>()
            val vusInt = mutableSetOf<String>()
            val vusLis = mutableSetOf<String>()
            var distPlusProche = Double.POSITIVE_INFINITY

            for (i in 0 until features.length()) {
                val feat = features.getJSONObject(i)
                val props = feat.optJSONObject("properties") ?: continue
                val geom = feat.optJSONObject("geometry")
                val tfv = props.optString("tfv").ifEmpty { props.optString("libelle") }
                val essence = props.optString("essence")
                if (tfv.isEmpty() && essence.isEmpty()) continue

                val distM = distancePointGeometrieM(longitude, latitude, geom)
                if (distM < distPlusProche) distPlusProche = distM
                val cle = "$tfv|$essence"

                if (distM <= 5.0) {
                    if (vusInt.add(cle)) {
                        interieur.add(PeuplementForestier(tfv, essence, round1(distM)))
                    }
                } else if (distM <= 25.0) {
                    if (vusLis.add(cle)) {
                        lisiere.add(PeuplementForestier(tfv, essence, round1(distM)))
                    }
                }
            }

            val enBois = interieur.isNotEmpty()
            val enLis = !enBois && lisiere.isNotEmpty()
            ProfilForet(
                enZoneBoisee = enBois,
                enLisiere = enLis,
                distanceForetM = if (distPlusProche.isFinite()) round1(distPlusProche) else null,
                peuplements = interieur,
                peuplementsLisiere = if (enLis) lisiere else emptyList()
            )
        } catch (_: Exception) {
            ProfilForet(false, false, null, emptyList())
        }
    }

    fun recupererDonneesSol(latitude: Double, longitude: Double, foret: ProfilForet): ProfilSol {
        val essencesTxt = foret.peuplements.joinToString(" ") { "${it.formationVegetale} ${it.essence}" }.lowercase()
        val (ph, argile, sable, limon, soc) = when {
            listOf("pin", "conifère", "épicéa", "sapin", "lande").any { essencesTxt.contains(it) } ->
                listOf(5.1, 15.0, 58.0, 27.0, 45.0)
            essencesTxt.contains("châtaignier") ->
                listOf(5.2, 18.0, 42.0, 40.0, 42.0)
            listOf("hêtre", "chêne", "feuillus").any { essencesTxt.contains(it) } ->
                listOf(5.8, 22.0, 33.0, 45.0, 38.0)
            else ->
                listOf(6.5, 20.0, 35.0, 45.0, 25.0)
        }

        val texture = when {
            sable >= 55.0 -> "Sableux (drainant)"
            argile >= 32.0 -> "Argileux (rétenteur d'eau)"
            else -> "Limono-argilo-sableux (équilibré)"
        }
        val acidite = when {
            ph < 5.3 -> "fortement acide (siliceux)"
            ph < 6.4 -> "légèrement acide"
            ph <= 7.2 -> "neutre"
            else -> "calcaire (basique)"
        }

        return ProfilSol(
            ph = ph,
            argilePct = argile,
            sablePct = sable,
            limonPct = limon,
            carboneOrganiqueGKg = soc,
            typeSol = "$texture, $acidite",
            source = "Bio-indication pédologique & IGN"
        )
    }

    suspend fun recupererDonneesMeteo(latitude: Double, longitude: Double, pastDays: Int = 20, forecastDays: Int = 11): SerieMeteo {
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        val dateJour = sdf.format(Calendar.getInstance().time)
        val latMaille = String.format(Locale.US, "%.2f", latitude)
        val lonMaille = String.format(Locale.US, "%.2f", longitude)
        val cleCache = "$latMaille:$lonMaille:$dateJour"

        cacheMeteo[cleCache]?.let { return it }

        val urlComplete = "https://api.open-meteo.com/v1/forecast" +
            "?latitude=$latitude&longitude=$longitude" +
            "&daily=precipitation_sum,temperature_2m_mean,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,et0_fao_evapotranspiration" +
            "&hourly=soil_temperature_6cm,soil_moisture_0_to_7cm,relative_humidity_2m" +
            "&past_days=$pastDays&forecast_days=$forecastDays"

        for (delaiMs in listOf(0L, 600L, 1300L)) {
            if (delaiMs > 0) delay(delaiMs)
            val resp = httpGet(urlComplete, 10000)
            if (resp != null) {
                parseMeteoResponse(resp, pastDays)?.let {
                    cacheMeteo[cleCache] = it
                    return it
                }
            }
        }

        // Repli sur requête journalière allégée
        val urlLegere = "https://api.open-meteo.com/v1/forecast" +
            "?latitude=$latitude&longitude=$longitude" +
            "&daily=precipitation_sum,temperature_2m_mean,temperature_2m_max,temperature_2m_min,wind_speed_10m_max,et0_fao_evapotranspiration" +
            "&past_days=$pastDays&forecast_days=$forecastDays"
        val respLegere = httpGet(urlLegere, 9000)
        if (respLegere != null) {
            parseMeteoResponse(respLegere, pastDays)?.let {
                cacheMeteo[cleCache] = it
                return it
            }
        }

        // Repli sur cache voisin ou profil saisonnier
        cacheMeteo.values.firstOrNull()?.let { return it }
        return genererMeteoSecours(pastDays, forecastDays)
    }

    private fun parseMeteoResponse(jsonStr: String, pastDays: Int): SerieMeteo? {
        return try {
            val root = JSONObject(jsonStr)
            val daily = root.optJSONObject("daily") ?: return null
            val hourly = root.optJSONObject("hourly")

            val timeArr = daily.optJSONArray("time") ?: return null
            val n = timeArr.length()
            if (n < 21) return null

            val dates = (0 until n).map { timeArr.optString(it) }
            val precips = extraireDoubleList(daily.optJSONArray("precipitation_sum"), n, 0.0)
            val tMean = extraireDoubleList(daily.optJSONArray("temperature_2m_mean"), n, 11.0)
            val tMax = extraireDoubleList(daily.optJSONArray("temperature_2m_max"), n, 15.0)
            val tMin = extraireDoubleList(daily.optJSONArray("temperature_2m_min"), n, 7.0)
            val wind = extraireDoubleList(daily.optJSONArray("wind_speed_10m_max"), n, 11.0)
            val et0 = extraireDoubleList(daily.optJSONArray("et0_fao_evapotranspiration"), n, 1.2)

            val sol6 = extraireMoyennes24h(hourly?.optJSONArray("soil_temperature_6cm"), n)
                ?: (0 until n).map { i -> round1(tMean.subList(max(0, i - 5), i + 1).average() + 0.9) }

            val humSol = extraireMoyennes24h(hourly?.optJSONArray("soil_moisture_0_to_7cm"), n)
                ?: run {
                    var h = 0.25
                    (0 until n).map { i ->
                        h = (h + 0.0085 * precips[i] - 0.012 * et0[i]).coerceIn(0.11, 0.45)
                        round3(h)
                    }
                }

            val hrAir = extraireMoyennes24h(hourly?.optJSONArray("relative_humidity_2m"), n)
                ?: (0 until n).map { i ->
                    val amp = max(0.0, tMax[i] - tMin[i] - 4.0)
                    (88.0 - 1.8 * amp + if (precips[i] >= 2.0) 6.0 else 0.0).coerceIn(48.0, 98.0)
                }

            SerieMeteo(
                dates = dates,
                precipitationSum = precips,
                soilTemperature6cm = sol6,
                soilMoisture0To7cm = humSol,
                temperature2mMin = tMin,
                windSpeed10mMax = wind,
                et0FaoEvapotranspiration = et0,
                relativeHumidity2m = hrAir,
                indexAujourdHui = pastDays
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun extraireDoubleList(arr: JSONArray?, n: Int, defaut: Double): List<Double> {
        if (arr == null) return List(n) { defaut }
        return (0 until n).map { i ->
            val v = arr.optDouble(i, defaut)
            if (v.isNaN()) defaut else v
        }
    }

    private fun extraireMoyennes24h(arr: JSONArray?, nDays: Int): List<Double>? {
        if (arr == null || arr.length() < nDays * 24) return null
        return (0 until nDays).map { d ->
            var sum = 0.0
            var count = 0
            for (h in 0 until 24) {
                val v = arr.optDouble(d * 24 + h, Double.NaN)
                if (!v.isNaN()) {
                    sum += v
                    count++
                }
            }
            if (count > 0) (sum / count * 100.0).roundToInt() / 100.0 else 10.0
        }
    }

    fun genererMeteoSecours(pastDays: Int = 20, forecastDays: Int = 11): SerieMeteo {
        val total = pastDays + forecastDays
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        val cal = Calendar.getInstance()
        val mois = cal.get(Calendar.MONTH) + 1
        cal.add(Calendar.DAY_OF_YEAR, -pastDays)

        val dates = (0 until total).map {
            val d = sdf.format(cal.time)
            cal.add(Calendar.DAY_OF_YEAR, 1)
            d
        }
        val tBase = when (mois) {
            1 -> 4.0; 2 -> 5.5; 3 -> 9.0; 4 -> 12.0; 5 -> 15.5; 6 -> 18.5
            7 -> 21.0; 8 -> 20.5; 9 -> 16.5; 10 -> 12.5; 11 -> 9.5; else -> 5.0
        }
        val precips = (0 until total).map { i ->
            when (i) {
                in 8..13 -> 8.5
                in 22..25 -> 14.0
                else -> 0.0
            }
        }
        val sol6 = List(total) { round1(tBase + 1.0) }
        val humSol = List(total) { 0.29 }
        val tMin = List(total) { round1(tBase - 3.5) }
        val wind = List(total) { 10.0 }
        val et0 = List(total) { 1.0 }
        val hr = List(total) { 84.0 }

        return SerieMeteo(dates, precips, sol6, humSol, tMin, wind, et0, hr, pastDays)
    }

    suspend fun chargerRapportSpot(latitude: Double, longitude: Double, nomSpot: String): RapportSimulation =
        withContext(Dispatchers.IO) {
            val defTopo = async { recupererTopographie(latitude, longitude) }
            val defForet = async { recupererForetIgn(latitude, longitude) }
            val defMeteo = async { recupererDonneesMeteo(latitude, longitude) }

            val topo = defTopo.await()
            val foret = defForet.await()
            val sol = recupererDonneesSol(latitude, longitude, foret)
            val meteo = defMeteo.await()

            ModeleMycologique.executerSimulationComplete(
                latitude = latitude,
                longitude = longitude,
                nomSpot = nomSpot,
                topo = topo,
                sol = sol,
                foret = foret,
                meteo = meteo
            )
        }

    private fun round1(v: Double): Double = (v * 10.0).roundToInt() / 10.0
    private fun round2(v: Double): Double = (v * 100.0).roundToInt() / 100.0
    private fun round3(v: Double): Double = (v * 1000.0).roundToInt() / 1000.0
}
