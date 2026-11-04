package fr.geekage.champignons.ui.main

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.view.MotionEvent
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import fr.geekage.champignons.data.ApiEnvironnementMeteo
import fr.geekage.champignons.model.*
import fr.geekage.champignons.ui.theme.SimulateurChampignonsTheme
import java.util.Locale

@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit = {},
    modifier: Modifier = Modifier,
    viewModel: MainScreenViewModel = viewModel { MainScreenViewModel() }
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    val launcherPermissionGps = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { perms ->
        val accorde = perms[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            perms[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        if (accorde) {
            obtenirPositionGpsLocale(context)?.let { (lat, lon) ->
                viewModel.simulerPointGps(lat, lon, "📍 Ma position GPS")
            }
        }
    }

    SimulateurChampignonsContent(
        state = state,
        modifier = modifier,
        onGpsClick = {
            val hasPerm = ContextCompat.checkSelfPermission(
                context, Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED || ContextCompat.checkSelfPermission(
                context, Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

            if (hasPerm) {
                val loc = obtenirPositionGpsLocale(context)
                if (loc != null) {
                    viewModel.simulerPointGps(loc.first, loc.second, "📍 Ma position GPS")
                } else {
                    viewModel.simulerPointGps(45.4105, 5.2400, "📍 Position GPS (Isère)")
                }
            } else {
                launcherPermissionGps.launch(
                    arrayOf(
                        Manifest.permission.ACCESS_FINE_LOCATION,
                        Manifest.permission.ACCESS_COARSE_LOCATION
                    )
                )
            }
        },
        onSelectJour = viewModel::changerJourSelectionne,
        onSearchChange = viewModel::changerRecherche,
        onFiltreChange = viewModel::changerFiltreMode,
        onTabChange = viewModel::changerOnglet,
        onSimulerCoords = { lat, lon, nom ->
            viewModel.simulerPointGps(lat, lon, nom)
        },
        onSauvegarderSpot = viewModel::ajouterSpotActuelAuxFavoris,
        onSelectEspece = viewModel::selectionnerEspeceDetail,
        onScanner5km = viewModel::scannerZonesEspece5km,
        onEffacerScan5km = viewModel::effacerScan5km
    )
}

@SuppressLint("MissingPermission")
private fun obtenirPositionGpsLocale(context: Context): Pair<Double, Double>? {
    return try {
        val lm = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val loc = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER)
            ?: lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
            ?: lm.getLastKnownLocation(LocationManager.PASSIVE_PROVIDER)
        loc?.let { it.latitude to it.longitude }
    } catch (_: Exception) {
        null
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SimulateurChampignonsContent(
    state: SimulateurUiState,
    modifier: Modifier = Modifier,
    onGpsClick: () -> Unit = {},
    onSelectJour: (Int) -> Unit = {},
    onSearchChange: (String) -> Unit = {},
    onFiltreChange: (String) -> Unit = {},
    onTabChange: (Int) -> Unit = {},
    onSimulerCoords: (Double, Double, String?) -> Unit = { _, _, _ -> },
    onSauvegarderSpot: (String) -> Unit = {},
    onSelectEspece: (ResultatEspece?) -> Unit = {},
    onScanner5km: (EspeceChampignon) -> Unit = {},
    onEffacerScan5km: () -> Unit = {}
) {
    var afficherDialogFavori by remember { mutableStateOf(false) }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "🍄 Simulateur Champignons",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFE7F3EA)
                        )
                        Text(
                            text = state.rapport.nomSpot,
                            fontSize = 12.sp,
                            color = Color(0xFF4ADE80),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                },
                actions = {
                    if (state.isLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier
                                .size(22.dp)
                                .padding(end = 8.dp),
                            strokeWidth = 2.5.dp,
                            color = Color(0xFF4ADE80)
                        )
                    }
                    FilledTonalButton(
                        onClick = onGpsClick,
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                        colors = ButtonDefaults.filledTonalButtonColors(
                            containerColor = Color(0xFF1E3F29),
                            contentColor = Color(0xFF4ADE80)
                        ),
                        modifier = Modifier.padding(end = 6.dp)
                    ) {
                        Text("📍 GPS", fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                    OutlinedButton(
                        onClick = { afficherDialogFavori = true },
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp),
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        Text("⭐+", fontSize = 12.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF132218)
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = Color(0xFF132218),
                tonalElevation = 8.dp
            ) {
                NavigationBarItem(
                    selected = state.ongletActif == 0,
                    onClick = { onTabChange(0) },
                    icon = { Text("🍄", fontSize = 18.sp) },
                    label = { Text("Prévisions J..J+10", fontSize = 11.sp) }
                )
                NavigationBarItem(
                    selected = state.ongletActif == 1,
                    onClick = { onTabChange(1) },
                    icon = { Text("🗺️", fontSize = 18.sp) },
                    label = { Text("Grande Carte", fontSize = 11.sp) }
                )
                NavigationBarItem(
                    selected = state.ongletActif == 2,
                    onClick = { onTabChange(2) },
                    icon = { Text("⭐", fontSize = 18.sp) },
                    label = { Text("Mes Coins (${state.spotsFavoris.size})", fontSize = 11.sp) }
                )
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF0F1912))
                .padding(innerPadding)
        ) {
            when (state.ongletActif) {
                0 -> OngletPrevisions(
                    state = state,
                    onSelectJour = onSelectJour,
                    onSearchChange = onSearchChange,
                    onFiltreChange = onFiltreChange,
                    onSelectEspece = onSelectEspece,
                    onSimulerCoords = onSimulerCoords,
                    onOuvrirCarte = { onTabChange(1) },
                    onScanner5km = onScanner5km,
                    onEffacerScan5km = onEffacerScan5km
                )
                1 -> OngletCarteEtBiotope(
                    rapport = state.rapport,
                    resultatScan5km = state.resultatScan5km,
                    isScanning5km = state.isScanning5km,
                    onSimulerCoords = { lat, lon, nom ->
                        onSimulerCoords(lat, lon, nom)
                    },
                    onVoirPrevisions = { onTabChange(0) },
                    onScanner5km = onScanner5km,
                    onEffacerScan5km = onEffacerScan5km
                )
                2 -> OngletSpotsFavoris(
                    spots = state.spotsFavoris,
                    onChargerSpot = { spot ->
                        onSimulerCoords(spot.latitude, spot.longitude, spot.nom)
                        onTabChange(0)
                    },
                    onAjouterCoinActuel = { afficherDialogFavori = true }
                )
            }
        }
    }

    if (afficherDialogFavori) {
        DialogAjouterFavori(
            nomParDefaut = state.rapport.nomSpot,
            onDismiss = { afficherDialogFavori = false },
            onConfirm = { nom ->
                onSauvegarderSpot(nom)
                afficherDialogFavori = false
            }
        )
    }

    state.especeSelectionnee?.let { esp ->
        DialogDetailEspece(
            especeResultat = esp,
            onDismiss = { onSelectEspece(null) },
            onScanner5km = { onScanner5km(esp.espece) }
        )
    }
}

@Composable
private fun OngletPrevisions(
    state: SimulateurUiState,
    onSelectJour: (Int) -> Unit,
    onSearchChange: (String) -> Unit,
    onFiltreChange: (String) -> Unit,
    onSelectEspece: (ResultatEspece) -> Unit,
    onSimulerCoords: (Double, Double, String?) -> Unit,
    onOuvrirCarte: () -> Unit,
    onScanner5km: (EspeceChampignon) -> Unit,
    onEffacerScan5km: () -> Unit
) {
    val rapport = state.rapport
    val idxJour = state.jourSelectionneIndex.coerceIn(0, 10)
    var afficherCarteHaut by remember { mutableStateOf(true) }
    var focusCoords by remember { mutableStateOf<Pair<Double, Double>?>(null) }

    val especesFiltrees = remember(rapport, state.rechercheTexte, state.filtreMode, idxJour) {
        rapport.especesProbables.filter { item ->
            val matchTxt = state.rechercheTexte.isBlank() ||
                item.espece.nom.contains(state.rechercheTexte, ignoreCase = true) ||
                item.espece.nomScientifique.contains(state.rechercheTexte, ignoreCase = true)
            val jourData = item.courbeJaJ10.getOrNull(idxJour)
            val st = jourData?.details?.stadesCarpophore
            val matchFiltre = when (state.filtreMode) {
                "FAVORABLE" -> (jourData?.scorePct ?: 0) >= 50 || item.scoreMaxJ10Pct >= 55
                "EN_POUSSE" -> (jourData?.scorePct ?: 0) >= 15 && (st?.enPoussePct ?: 0) >= 30
                "ADULTES" -> (jourData?.scorePct ?: 0) >= 15 && (st?.adultesPct ?: 0) >= 30
                else -> true
            }
            matchTxt && matchFiltre
        }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        // 1. Carte interactive directement visible en haut de l'écran principal (repliable)
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF284030), RoundedCornerShape(12.dp))
            ) {
                Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "📍 Carte Interactive (${String.format(Locale.US, "%.4f, %.4f", rapport.latitude, rapport.longitude)})",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFE7F3EA)
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            TextButton(
                                onClick = { afficherCarteHaut = !afficherCarteHaut },
                                contentPadding = PaddingValues(horizontal = 6.dp, vertical = 0.dp)
                            ) {
                                Text(
                                    text = if (afficherCarteHaut) "Masquer ▲" else "Afficher ▼",
                                    fontSize = 11.sp,
                                    color = Color(0xFF94AD9C)
                                )
                            }
                            TextButton(
                                onClick = onOuvrirCarte,
                                contentPadding = PaddingValues(horizontal = 6.dp, vertical = 0.dp)
                            ) {
                                Text("Plein écran ⛶", fontSize = 11.sp, color = Color(0xFF4ADE80))
                            }
                        }
                    }

                    if (afficherCarteHaut) {
                        CarteInteractiveWebView(
                            latitude = rapport.latitude,
                            longitude = rapport.longitude,
                            hauteur = if (state.resultatScan5km != null) 280.dp else 215.dp,
                            resultatScan5km = state.resultatScan5km,
                            focusSpot = focusCoords,
                            onPointSelected = { lat, lon ->
                                onSimulerCoords(lat, lon, null)
                            }
                        )
                        Text(
                            text = "Touchez un point sur la carte pour simuler, ou appuyez sur « 🎯 Zones 5 km » sur une espèce ci-dessous.",
                            fontSize = 11.sp,
                            color = Color(0xFF8AA392)
                        )
                    }

                    if (state.isScanning5km) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = Color(0xFF4ADE80)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = state.messageStatut ?: "Scan topographique & IGN BD Forêt (5 km)...",
                                fontSize = 12.sp,
                                color = Color(0xFF4ADE80)
                            )
                        }
                    }

                    state.resultatScan5km?.let { scan ->
                        PanneauResultatsScan5km(
                            scan = scan,
                            onCentrerSpot = { lat, lon ->
                                afficherCarteHaut = true
                                focusCoords = lat to lon
                            },
                            onSimulerSpot = { lat, lon, nom ->
                                onSimulerCoords(lat, lon, nom)
                            },
                            onEffacer = onEffacerScan5km
                        )
                    }
                }
            }
        }

        // 2. Bandeau Synthèse Écologique du Spot
        item {
            BandeauBiotopeCompact(rapport = rapport, onChangerSpotClick = onOuvrirCarte)
        }

        // 3. Sélecteur horizontal des 11 jours (J à J+10)
        item {
            SelecteurJoursHorizontal(
                rapport = rapport,
                jourSelectionneIndex = idxJour,
                onSelectJour = onSelectJour
            )
        }

        // 4. Barre de recherche & Filtres par Stade de Maturité
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = state.rechercheTexte,
                    onValueChange = onSearchChange,
                    placeholder = { Text("Rechercher (Cèpe, Coulemelle, Girolle, Trompette...)", fontSize = 13.sp) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp)
                )

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    FiltreChipItem("Toutes (${rapport.especesProbables.size})", state.filtreMode == "TOUS") {
                        onFiltreChange("TOUS")
                    }
                    FiltreChipItem("🔥 Favorables ≥50%", state.filtreMode == "FAVORABLE") {
                        onFiltreChange("FAVORABLE")
                    }
                    FiltreChipItem("🌱 En pousse", state.filtreMode == "EN_POUSSE") {
                        onFiltreChange("EN_POUSSE")
                    }
                    FiltreChipItem("🍄 Adultes", state.filtreMode == "ADULTES") {
                        onFiltreChange("ADULTES")
                    }
                }
            }
        }

        // 5. Liste des cartes d'espèces
        items(especesFiltrees, key = { it.espece.id }) { item ->
            CarteEspeceMobile(
                item = item,
                jourIndex = idxJour,
                onClick = { onSelectEspece(item) },
                onScanner5km = { onScanner5km(item.espece) }
            )
        }
    }
}

@Composable
private fun PanneauResultatsScan5km(
    scan: ResultatScan5km,
    onCentrerSpot: (Double, Double) -> Unit,
    onSimulerSpot: (Double, Double, String) -> Unit,
    onEffacer: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(Color(0xFF101D15))
            .border(1.dp, Color(0xFF2D6A4F), RoundedCornerShape(10.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "🎯 Zones 5 km : ${scan.espece.nom} (${scan.echeance})",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF4ADE80)
                )
                Text(
                    text = "${scan.zonesOptimales.size} meilleurs secteurs sur ${scan.nbPointsTestes} analysés (${scan.nbParcellesIgn} parcelles IGN)",
                    fontSize = 11.sp,
                    color = Color(0xFF94AD9C)
                )
            }
            TextButton(
                onClick = onEffacer,
                contentPadding = PaddingValues(horizontal = 6.dp, vertical = 0.dp)
            ) {
                Text("Effacer ✕", fontSize = 11.sp, color = Color(0xFFE76F51))
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            scan.zonesOptimales.take(12).forEach { z ->
                val col = couleurPourScore(z.scorePct)
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF182A1E)),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier
                        .width(235.dp)
                        .border(1.dp, col.copy(alpha = 0.6f), RoundedCornerShape(10.dp))
                        .clickable { onCentrerSpot(z.latitude, z.longitude) }
                ) {
                    Column(
                        modifier = Modifier.padding(9.dp),
                        verticalArrangement = Arrangement.spacedBy(3.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "#${z.rang} • ${z.distanceKm} km (${z.directionCardinale})",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFFE7F3EA)
                            )
                            Text(
                                text = "${z.scorePct}%",
                                fontSize = 14.sp,
                                fontWeight = FontWeight.ExtraBold,
                                color = col
                            )
                        }
                        Text(
                            text = z.libelleBiotope,
                            fontSize = 11.sp,
                            color = Color(0xFF4ADE80),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Text(
                            text = "⛰️ ${z.altitudeM.toInt()}m • ${z.orientation.substringBefore(" (")} (${z.penteDeg}°) • pH ${z.phEstime}",
                            fontSize = 10.sp,
                            color = Color(0xFF94AD9C),
                            maxLines = 1
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "${z.stadesCarpophore.icone} ${z.stadesCarpophore.labelCourt}",
                                fontSize = 10.sp,
                                color = Color(0xFFE7F3EA)
                            )
                            Text(
                                text = "📍 Simuler →",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF4ADE80),
                                modifier = Modifier.clickable {
                                    onSimulerSpot(
                                        z.latitude,
                                        z.longitude,
                                        "Spot #${z.rang} ${scan.espece.nom} (${z.distanceKm}km ${z.directionCardinale})"
                                    )
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled", "ClickableViewAccessibility")
@Composable
fun CarteInteractiveWebView(
    latitude: Double,
    longitude: Double,
    hauteur: Dp,
    resultatScan5km: ResultatScan5km? = null,
    focusSpot: Pair<Double, Double>? = null,
    onPointSelected: (Double, Double) -> Unit
) {
    val currentOnPointSelected by rememberUpdatedState(onPointSelected)
    val jsonScan = remember(resultatScan5km) {
        resultatScan5km?.let { ApiEnvironnementMeteo.convertirScan5kmEnJsonLeaflet(it) } ?: ""
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(hauteur)
            .clip(RoundedCornerShape(10.dp))
            .border(1.dp, Color(0xFF284030), RoundedCornerShape(10.dp))
    ) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                WebView(ctx).apply {
                    layoutParams = ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    settings.apply {
                        javaScriptEnabled = true
                        domStorageEnabled = true
                        databaseEnabled = true
                        loadWithOverviewMode = true
                        useWideViewPort = true
                        mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                        userAgentString = "SimulateurChampignons/1.1 (Android; Mobile)"
                    }
                    webViewClient = object : WebViewClient() {
                        override fun onPageFinished(view: WebView?, url: String?) {
                            super.onPageFinished(view, url)
                            if (jsonScan.isNotEmpty()) {
                                val escaped = jsonScan.replace("\\", "\\\\").replace("'", "\\'")
                                view?.evaluateJavascript("if(window.afficherZones5km){window.afficherZones5km('$escaped');}", null)
                            }
                        }
                    }

                    setOnTouchListener { v, event ->
                        when (event.action) {
                            MotionEvent.ACTION_DOWN, MotionEvent.ACTION_MOVE ->
                                v.parent?.requestDisallowInterceptTouchEvent(true)
                            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL ->
                                v.parent?.requestDisallowInterceptTouchEvent(false)
                        }
                        false
                    }

                    addJavascriptInterface(
                        object {
                            @JavascriptInterface
                            fun onMapTapped(lat: Double, lon: Double) {
                                post {
                                    currentOnPointSelected(lat, lon)
                                }
                            }
                        },
                        "AndroidBridge"
                    )

                    tag = Triple("$latitude,$longitude", jsonScan.hashCode(), focusSpot)
                    loadDataWithBaseURL(
                        "https://simulateur-champignons.local/",
                        construireHtmlCarteLeaflet(latitude, longitude),
                        "text/html",
                        "UTF-8",
                        null
                    )
                }
            },
            update = { webView ->
                val oldTriple = webView.tag as? Triple<*, *, *>
                val newCoord = "$latitude,$longitude"
                val newScanHash = jsonScan.hashCode()

                if (oldTriple?.first != newCoord) {
                    webView.evaluateJavascript("if(window.centrerCarte){window.centrerCarte($latitude, $longitude);}", null)
                }
                if (oldTriple?.second != newScanHash) {
                    if (jsonScan.isEmpty()) {
                        webView.evaluateJavascript("if(window.effacerZones5km){window.effacerZones5km();}", null)
                    } else {
                        val escaped = jsonScan.replace("\\", "\\\\").replace("'", "\\'")
                        webView.evaluateJavascript("if(window.afficherZones5km){window.afficherZones5km('$escaped');}", null)
                    }
                }
                if (focusSpot != null && oldTriple?.third != focusSpot) {
                    webView.evaluateJavascript("if(window.zoomerSpot5km){window.zoomerSpot5km(${focusSpot.first}, ${focusSpot.second});}", null)
                }
                webView.tag = Triple(newCoord, newScanHash, focusSpot)
            }
        )
    }
}

@Composable
private fun BandeauBiotopeCompact(
    rapport: RapportSimulation,
    onChangerSpotClick: () -> Unit
) {
    val badgeHabitat = when {
        rapport.foret.enZoneBoisee -> {
            val premier = rapport.foret.peuplements.firstOrNull()
            "🌳 ${premier?.formationVegetale ?: "Forêt"} (${premier?.essence ?: "Boisement"})"
        }
        rapport.foret.enLisiere -> {
            val dist = rapport.foret.distanceForetM?.let { " à ${it.toInt()}m" } ?: ""
            "🌿 Prairie en lisière forestière (bois$dist)"
        }
        else -> "🌾 Prairie / Milieu ouvert (Hors forêt IGN)"
    }
    val couleurHabitat = when {
        rapport.foret.enZoneBoisee -> Color(0xFF4ADE80)
        rapport.foret.enLisiere -> Color(0xFFFBBF24)
        else -> Color(0xFFA3E635)
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF23382A), RoundedCornerShape(12.dp))
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = badgeHabitat,
                    color = couleurHabitat,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
                TextButton(
                    onClick = onChangerSpotClick,
                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 0.dp)
                ) {
                    Text("Détails sol/forêt →", fontSize = 11.sp, color = Color(0xFF4ADE80))
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                InfoMiniStat("⛰️ Alt / Pente", "${rapport.topographie.altitudeM.toInt()}m • ${rapport.topographie.penteDeg}°")
                InfoMiniStat("🧭 Versant", rapport.topographie.orientation.substringBefore(" ("))
                InfoMiniStat("🧪 Sol (0-5cm)", "pH ${rapport.sol.ph}")
                InfoMiniStat("🌧️ Pluie 20j / +10j", "${rapport.cumulPluie20jMm.toInt()} / ${rapport.cumulPluiePrevue10jMm.toInt()}mm")
            }
        }
    }
}

@Composable
private fun InfoMiniStat(label: String, valeur: String) {
    Column {
        Text(text = label, fontSize = 10.sp, color = Color(0xFF8AA392))
        Text(text = valeur, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFFE7F3EA))
    }
}

@Composable
private fun SelecteurJoursHorizontal(
    rapport: RapportSimulation,
    jourSelectionneIndex: Int,
    onSelectJour: (Int) -> Unit
) {
    val joursReference = rapport.especesProbables.firstOrNull()?.courbeJaJ10 ?: return

    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = "📅 Échéance affichée (glissez de J à J+10) :",
            fontSize = 12.sp,
            color = Color(0xFF94AD9C),
            fontWeight = FontWeight.Medium
        )
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            joursReference.forEachIndexed { idx, sj ->
                val estSelectionne = idx == jourSelectionneIndex
                val jjMm = if (sj.date.length >= 10) "${sj.date.substring(8, 10)}/${sj.date.substring(5, 7)}" else sj.date
                Surface(
                    shape = RoundedCornerShape(10.dp),
                    color = if (estSelectionne) Color(0xFF22C55E) else Color(0xFF18281E),
                    modifier = Modifier
                        .border(
                            width = 1.dp,
                            color = if (estSelectionne) Color(0xFF4ADE80) else Color(0xFF284030),
                            shape = RoundedCornerShape(10.dp)
                        )
                        .clickable { onSelectJour(idx) }
                ) {
                    Column(
                        modifier = Modifier.padding(horizontal = 11.dp, vertical = 6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = sj.echeance,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = if (estSelectionne) Color(0xFF052E16) else Color(0xFFE7F3EA)
                        )
                        Text(
                            text = jjMm,
                            fontSize = 10.sp,
                            color = if (estSelectionne) Color(0xFF052E16) else Color(0xFF8AA392)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun FiltreChipItem(label: String, selected: Boolean, onClick: () -> Unit) {
    FilterChip(
        selected = selected,
        onClick = onClick,
        label = { Text(label, fontSize = 12.sp) },
        colors = FilterChipDefaults.filterChipColors(
            selectedContainerColor = Color(0xFF1F472B),
            selectedLabelColor = Color(0xFF4ADE80)
        )
    )
}

@Composable
fun CarteEspeceMobile(
    item: ResultatEspece,
    jourIndex: Int,
    onClick: () -> Unit,
    onScanner5km: () -> Unit = {}
) {
    val scoreJour = item.courbeJaJ10.getOrNull(jourIndex) ?: item.courbeJaJ10.first()
    val stades = scoreJour.details.stadesCarpophore
    val couleurBadge = couleurPourScore(scoreJour.scorePct)

    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
        shape = RoundedCornerShape(14.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF23382A), RoundedCornerShape(14.dp))
            .clickable { onClick() }
    ) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = item.espece.nom,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFFE7F3EA)
                    )
                    Text(
                        text = "${item.espece.nomScientifique} • ${item.espece.typeTrophique.label} • Biotope ${item.compatibiliteBiotopePct}%",
                        fontSize = 11.sp,
                        fontStyle = FontStyle.Italic,
                        color = Color(0xFF8AA392)
                    )
                    Surface(
                        color = Color(0xFF1F3E2B),
                        shape = RoundedCornerShape(6.dp),
                        modifier = Modifier
                            .padding(top = 4.dp)
                            .border(1.dp, Color(0xFF4ADE80).copy(alpha = 0.55f), RoundedCornerShape(6.dp))
                            .clickable { onScanner5km() }
                    ) {
                        Text(
                            text = "🎯 Zones 5 km",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF4ADE80),
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                        )
                    }
                }

                Surface(
                    color = couleurBadge.copy(alpha = 0.20f),
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier.border(1.dp, couleurBadge, RoundedCornerShape(10.dp))
                ) {
                    Column(
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "${scoreJour.scorePct}%",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = couleurBadge
                        )
                        Text(
                            text = scoreJour.echeance,
                            fontSize = 10.sp,
                            color = couleurBadge
                        )
                    }
                }
            }

            if (scoreJour.scorePct >= 10 && stades.icone != "—") {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(Color(0xFF111C15))
                        .padding(8.dp),
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "${stades.icone} ${stades.labelCourt}",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = Color(0xFFE7F3EA)
                        )
                        Text(
                            text = "🚀 ${scoreJour.details.vitessePousse}",
                            fontSize = 11.sp,
                            color = Color(0xFF4ADE80)
                        )
                    }

                    BarreStadesTricolore(stades = stades, hauteurDp = 6)

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("🌱 En pousse : ${stades.enPoussePct}%", fontSize = 10.sp, color = Color(0xFF4ADE80))
                        Text("🍄 Adultes : ${stades.adultesPct}%", fontSize = 10.sp, color = Color(0xFFFBBF24))
                        Text("🍂 Vieillissants : ${stades.vieillissantsPct}%", fontSize = 10.sp, color = Color(0xFFF97316))
                    }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Bottom
            ) {
                item.courbeJaJ10.forEachIndexed { idx, sj ->
                    val estActif = idx == jourIndex
                    val col = couleurPourScore(sj.scorePct)
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(
                            text = "${sj.scorePct}",
                            fontSize = 9.sp,
                            fontWeight = if (estActif) FontWeight.Bold else FontWeight.Normal,
                            color = if (estActif) Color.White else Color(0xFF8AA392)
                        )
                        Box(
                            modifier = Modifier
                                .width(14.dp)
                                .height((4 + (sj.scorePct * 0.22)).dp)
                                .clip(RoundedCornerShape(3.dp))
                                .background(if (estActif) col else col.copy(alpha = 0.55f))
                        )
                        Text(
                            text = sj.echeance,
                            fontSize = 8.sp,
                            color = if (estActif) Color(0xFF4ADE80) else Color(0xFF6E8575)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun BarreStadesTricolore(stades: StadesCarpophore, hauteurDp: Int = 6) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .height(hauteurDp.dp)
            .clip(RoundedCornerShape(3.dp))
            .background(Color(0xFF1F2E22))
    ) {
        if (stades.enPoussePct > 0) {
            Box(
                modifier = Modifier
                    .weight(stades.enPoussePct.toFloat())
                    .fillMaxHeight()
                    .background(Color(0xFF4ADE80))
            )
        }
        if (stades.adultesPct > 0) {
            Box(
                modifier = Modifier
                    .weight(stades.adultesPct.toFloat())
                    .fillMaxHeight()
                    .background(Color(0xFFFBBF24))
            )
        }
        if (stades.vieillissantsPct > 0) {
            Box(
                modifier = Modifier
                    .weight(stades.vieillissantsPct.toFloat())
                    .fillMaxHeight()
                    .background(Color(0xFFF97316))
            )
        }
    }
}

@Composable
private fun OngletCarteEtBiotope(
    rapport: RapportSimulation,
    resultatScan5km: ResultatScan5km?,
    isScanning5km: Boolean,
    onSimulerCoords: (Double, Double, String?) -> Unit,
    onVoirPrevisions: () -> Unit,
    onScanner5km: (EspeceChampignon) -> Unit,
    onEffacerScan5km: () -> Unit
) {
    var latInput by remember(rapport.latitude) { mutableStateOf(String.format(Locale.US, "%.4f", rapport.latitude)) }
    var lonInput by remember(rapport.longitude) { mutableStateOf(String.format(Locale.US, "%.4f", rapport.longitude)) }
    var focusCoords by remember { mutableStateOf<Pair<Double, Double>?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "🗺️ Touchez la carte (Plan, Photo aérienne IGN ou Topo) :",
                fontSize = 13.sp,
                color = Color(0xFFE7F3EA),
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.weight(1f)
            )
            TextButton(onClick = onVoirPrevisions) {
                Text("Voir les 42 espèces →", fontSize = 12.sp, color = Color(0xFF4ADE80))
            }
        }

        CarteInteractiveWebView(
            latitude = rapport.latitude,
            longitude = rapport.longitude,
            hauteur = 360.dp,
            resultatScan5km = resultatScan5km,
            focusSpot = focusCoords,
            onPointSelected = { lat, lon ->
                onSimulerCoords(lat, lon, null)
            }
        )

        if (isScanning5km) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp, color = Color(0xFF4ADE80))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Scan 5 km en cours...", fontSize = 12.sp, color = Color(0xFF4ADE80))
            }
        }

        resultatScan5km?.let { scan ->
            PanneauResultatsScan5km(
                scan = scan,
                onCentrerSpot = { lat, lon -> focusCoords = lat to lon },
                onSimulerSpot = { lat, lon, nom -> onSimulerCoords(lat, lon, nom) },
                onEffacer = onEffacerScan5km
            )
        }

        // Sélecteur rapide d'espèce pour scanner à 5 km depuis la grande carte
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    text = "🎯 Scanner les meilleures zones dans un rayon de 5 km :",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF4ADE80)
                )
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    rapport.especesProbables.take(15).forEach { item ->
                        val estActive = resultatScan5km?.espece?.id == item.espece.id
                        FilterChip(
                            selected = estActive,
                            onClick = { onScanner5km(item.espece) },
                            label = { Text("🎯 ${item.espece.nom}", fontSize = 11.sp) }
                        )
                    }
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = latInput,
                onValueChange = { latInput = it },
                label = { Text("Latitude", fontSize = 11.sp) },
                singleLine = true,
                modifier = Modifier.weight(1f)
            )
            OutlinedTextField(
                value = lonInput,
                onValueChange = { lonInput = it },
                label = { Text("Longitude", fontSize = 11.sp) },
                singleLine = true,
                modifier = Modifier.weight(1f)
            )
            Button(
                onClick = {
                    val lat = latInput.replace(",", ".").toDoubleOrNull()
                    val lon = lonInput.replace(",", ".").toDoubleOrNull()
                    if (lat != null && lon != null) {
                        onSimulerCoords(lat, lon, null)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF22C55E))
            ) {
                Text("Simuler", color = Color(0xFF052E16), fontWeight = FontWeight.Bold)
            }
        }

        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("🌿 Diagnostic Écologique & Pédologique Détaillé", fontWeight = FontWeight.Bold, color = Color(0xFF4ADE80))
                HorizontalDivider(color = Color(0xFF23382A))
                Text("• Couvert & Habitat : ${rapport.microclimat.couvert}", fontSize = 13.sp, color = Color(0xFFE7F3EA))
                if (rapport.foret.peuplements.isNotEmpty()) {
                    rapport.foret.peuplements.forEach { p ->
                        Text("  🌳 ${p.formationVegetale} (${p.essence})", fontSize = 12.sp, color = Color(0xFF4ADE80))
                    }
                } else if (rapport.foret.enLisiere) {
                    rapport.foret.peuplementsLisiere.forEach { p ->
                        Text("  🌲 Lisière à ${p.distanceM} m : ${p.formationVegetale} (${p.essence})", fontSize = 12.sp, color = Color(0xFFFBBF24))
                    }
                }
                Text("• Topographie : Alt. ${rapport.topographie.altitudeM} m • Pente ${rapport.topographie.penteDeg}° (${rapport.topographie.pentePct}%)", fontSize = 13.sp)
                Text("• Exposition : ${rapport.topographie.orientation} (${if (rapport.topographie.deltaTempSolC >= 0) "+" else ""}${rapport.topographie.deltaTempSolC}°C sol)", fontSize = 13.sp)
                Text("• Sol : ${rapport.sol.typeSol} (pH ${rapport.sol.ph})", fontSize = 13.sp)
                Text("• Texture : Argile ${rapport.sol.argilePct.toInt()}% • Limon ${rapport.sol.limonPct.toInt()}% • Sable ${rapport.sol.sablePct.toInt()}%", fontSize = 12.sp, color = Color(0xFF8AA392))
                Text("• Tampon gel nocturne sous couvert : +${rapport.microclimat.tamponGelC}°C", fontSize = 12.sp, color = Color(0xFF8AA392))
            }
        }
    }
}

private fun construireHtmlCarteLeaflet(lat: Double, lon: Double): String {
    return """
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
          <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
          <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
          <style>
            * { box-sizing: border-box; }
            html, body { width: 100%; height: 100%; margin: 0; padding: 0; background: #16241b; overflow: hidden; }
            #map { position: absolute; top: 0; left: 0; right: 0; bottom: 0; width: 100vw; height: 100vh; }
          </style>
        </head>
        <body>
          <div id="map"></div>
          <script>
            var ignPlan = L.tileLayer(
              'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&FORMAT=image/png&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
              { maxZoom: 19, attribution: '© IGN' }
            );
            var ignOrtho = L.tileLayer(
              'https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}',
              { maxZoom: 19, attribution: '© IGN Ortho' }
            );
            var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
              maxZoom: 19,
              attribution: '© OSM'
            });
            var topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
              maxZoom: 17,
              attribution: '© OpenTopoMap'
            });

            var map = L.map('map', {
              center: [$lat, $lon],
              zoom: 14,
              layers: [ignPlan]
            });

            L.control.layers({
              "🗺️ Plan IGN France": ignPlan,
              "🛰️ Photo Aérienne Forêt/Pré (IGN)": ignOrtho,
              "🌍 OpenStreetMap": osm,
              "⛰️ Topographique (Courbes)": topo
            }).addTo(map);

            var marker = L.marker([$lat, $lon]).addTo(map);
            var couche5km = L.layerGroup().addTo(map);

            function couleurScore(s) {
              if (s >= 75) return '#22c55e';
              if (s >= 55) return '#84cc16';
              if (s >= 35) return '#eab308';
              if (s >= 15) return '#f97316';
              return '#64748b';
            }

            map.on('click', function(e) {
              marker.setLatLng(e.latlng);
              if (window.AndroidBridge && window.AndroidBridge.onMapTapped) {
                window.AndroidBridge.onMapTapped(e.latlng.lat, e.latlng.lng);
              }
            });

            window.centrerCarte = function(newLat, newLon) {
              var ll = L.latLng(newLat, newLon);
              marker.setLatLng(ll);
              map.panTo(ll);
            };

            window.effacerZones5km = function() {
              couche5km.clearLayers();
            };

            window.zoomerSpot5km = function(lat, lon) {
              map.setView([lat, lon], 14);
            };

            window.afficherZones5km = function(jsonStr) {
              try {
                var data = JSON.parse(jsonStr);
                couche5km.clearLayers();
                var cercle = L.circle([data.centreLat, data.centreLon], {
                  radius: data.rayonKm * 1000,
                  color: '#4ade80',
                  weight: 2,
                  dashArray: '6, 6',
                  fillColor: '#4ade80',
                  fillOpacity: 0.03
                }).addTo(couche5km);

                var zones = data.zones || [];
                for (var i = 0; i < zones.length; i++) {
                  var z = zones[i];
                  var c = couleurScore(z.score);
                  var popupHtml = '<b>#' + z.rang + ' • ' + data.nomEspece + ' : ' + z.score + '%</b><br/>' +
                    z.biotope + '<br/>' +
                    '📍 ' + z.distKm + ' km (' + z.dir + ') • Alt. ' + z.alt + 'm<br/>' +
                    '🧭 ' + z.orientation + ' (' + z.pente + '°)<br/>' +
                    '🍄 ' + z.stade;

                  if (z.poly && z.poly.length >= 3 && z.score >= 15) {
                    L.polygon(z.poly, {
                      color: c,
                      weight: 2,
                      fillColor: c,
                      fillOpacity: 0.28
                    }).bindPopup(popupHtml).addTo(couche5km);
                  } else if (z.score >= 15) {
                    L.circle([z.lat, z.lon], {
                      radius: 210,
                      color: c,
                      weight: 2,
                      fillColor: c,
                      fillOpacity: 0.28
                    }).addTo(couche5km);
                  }

                  var icone = L.divIcon({
                    className: '',
                    html: '<div style="background:' + c + ';color:#052e16;font-weight:800;font-size:10px;padding:2px 5px;border-radius:999px;border:1.5px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.5);white-space:nowrap;">#' + z.rang + ' • ' + z.score + '%</div>',
                    iconSize: [60, 20],
                    iconAnchor: [30, 10]
                  });
                  L.marker([z.lat, z.lon], { icon: icone }).bindPopup(popupHtml).addTo(couche5km);
                }
                map.fitBounds(cercle.getBounds(), { padding: [12, 12] });
              } catch (err) {
                console.error(err);
              }
            };

            setTimeout(function() { map.invalidateSize(); }, 150);
            setTimeout(function() { map.invalidateSize(); }, 500);
          </script>
        </body>
        </html>
    """.trimIndent()
}

@Composable
private fun OngletSpotsFavoris(
    spots: List<SpotPredefini>,
    onChargerSpot: (SpotPredefini) -> Unit,
    onAjouterCoinActuel: () -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "⭐ Mes Coins à Champignons & Massifs",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFE7F3EA)
                )
                Button(
                    onClick = onAjouterCoinActuel,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF22C55E))
                ) {
                    Text("+ Enregistrer ce point", color = Color(0xFF052E16), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }

        items(spots) { spot ->
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF16241B)),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, Color(0xFF23382A), RoundedCornerShape(12.dp))
                    .clickable { onChargerSpot(spot) }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "${spot.icone} ${spot.nom}",
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFE7F3EA)
                        )
                        Text(
                            text = "${spot.region} • (${String.format(Locale.US, "%.4f, %.4f", spot.latitude, spot.longitude)})",
                            fontSize = 12.sp,
                            color = Color(0xFF4ADE80)
                        )
                        Text(
                            text = spot.description,
                            fontSize = 12.sp,
                            color = Color(0xFF8AA392)
                        )
                    }
                    Text("Simuler →", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF4ADE80))
                }
            }
        }
    }
}

@Composable
private fun DialogDetailEspece(
    especeResultat: ResultatEspece,
    onDismiss: () -> Unit,
    onScanner5km: () -> Unit = {}
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF132218)),
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(max = 600.dp)
                .border(1.dp, Color(0xFF2D4A36), RoundedCornerShape(16.dp))
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = especeResultat.espece.nom,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF4ADE80)
                        )
                        Text(
                            text = "${especeResultat.espece.nomScientifique} • Biotope ${especeResultat.compatibiliteBiotopePct}%",
                            fontSize = 12.sp,
                            fontStyle = FontStyle.Italic,
                            color = Color(0xFF94AD9C)
                        )
                    }
                    TextButton(onClick = onDismiss) {
                        Text("Fermer ✕", color = Color(0xFFE7F3EA))
                    }
                }

                Button(
                    onClick = onScanner5km,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF22C55E)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 6.dp)
                ) {
                    Text(
                        text = "🎯 Voir les meilleures zones dans un rayon de 5 km",
                        color = Color(0xFF052E16),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                HorizontalDivider(color = Color(0xFF23382A), modifier = Modifier.padding(vertical = 6.dp))

                LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(especeResultat.courbeJaJ10) { j ->
                        val st = j.details.stadesCarpophore
                        val col = couleurPourScore(j.scorePct)
                        Card(
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF192B20)),
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = "${j.echeance} (${j.date})",
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        color = Color(0xFFE7F3EA)
                                    )
                                    Text(
                                        text = "${j.scorePct}%",
                                        fontWeight = FontWeight.ExtraBold,
                                        fontSize = 15.sp,
                                        color = col
                                    )
                                }
                                Text(
                                    text = "${st.icone} ${st.labelCourt} (🌱${st.enPoussePct}% • 🍄${st.adultesPct}% • 🍂${st.vieillissantsPct}%)",
                                    fontSize = 12.sp,
                                    color = Color(0xFFE7F3EA)
                                )
                                BarreStadesTricolore(stades = st, hauteurDp = 5)
                                Text(
                                    text = "🌧️ Pluie 20j : ${j.details.pluie20jMm}mm • 🌡️ Sol : ${j.details.tempSolC}°C (min ${j.details.tminSousBoisC}°C)",
                                    fontSize = 11.sp,
                                    color = Color(0xFF94AD9C)
                                )
                                Text(
                                    text = "⏱️ Maturation : ${j.details.delaiMaturationJ}j • 🚀 Pousse : ${j.details.vitessePousse}",
                                    fontSize = 11.sp,
                                    color = Color(0xFFFBBF24)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DialogAjouterFavori(
    nomParDefaut: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit
) {
    var nom by remember { mutableStateOf(nomParDefaut) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("⭐ Enregistrer ce coin à champignons") },
        text = {
            OutlinedTextField(
                value = nom,
                onValueChange = { nom = it },
                label = { Text("Nom du coin (ex: Châtaigneraie Nord)") },
                singleLine = true
            )
        },
        confirmButton = {
            Button(onClick = { onConfirm(nom) }) {
                Text("Enregistrer")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Annuler")
            }
        }
    )
}

private fun couleurPourScore(score: Int): Color = when {
    score >= 70 -> Color(0xFF4ADE80)
    score >= 45 -> Color(0xFFFBBF24)
    score >= 20 -> Color(0xFFF97316)
    else -> Color(0xFF64748B)
}

@Preview(showBackground = true, showSystemUi = true)
@Composable
fun MainScreenPreview() {
    SimulateurChampignonsTheme {
        SimulateurChampignonsContent(state = SimulateurUiState())
    }
}
