package fr.geekage.champignons.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import fr.geekage.champignons.data.ApiEnvironnementMeteo
import fr.geekage.champignons.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SimulateurUiState(
    val isLoading: Boolean = false,
    val rapport: RapportSimulation = creerRapportInitialDemo(),
    val jourSelectionneIndex: Int = 0,
    val rechercheTexte: String = "",
    val filtreMode: String = "TOUS", // "TOUS", "FAVORABLE", "EN_POUSSE", "ADULTES"
    val ongletActif: Int = 0, // 0 = Prévisions, 1 = Carte & Biotope, 2 = Mes Coins
    val especeSelectionnee: ResultatEspece? = null,
    val spotsFavoris: List<SpotPredefini> = ModeleMycologique.SPOTS_FAVORIS_DEFAUT,
    val messageStatut: String? = null
)

fun creerRapportInitialDemo(): RapportSimulation {
    val topo = ProfilTopographique(
        altitudeM = 510.0,
        penteDeg = 9.3,
        pentePct = 16.3,
        azimutDeg = 355.0,
        orientation = "Nord (Ubac frais)",
        deltaTempSolC = -0.83,
        coeffRetentionHumidite = 1.04,
        coeffInfiltrationPluie = 1.0
    )
    val foret = ProfilForet(
        enZoneBoisee = true,
        enLisiere = false,
        distanceForetM = 0.0,
        peuplements = listOf(
            PeuplementForestier("Forêt fermée de châtaignier pur", "Châtaignier", 0.0),
            PeuplementForestier("Forêt fermée à mélange de feuillus", "Feuillus", 0.0)
        )
    )
    val sol = ApiEnvironnementMeteo.recupererDonneesSol(45.4105, 5.2400, foret)
    val meteo = ApiEnvironnementMeteo.genererMeteoSecours()
    return ModeleMycologique.executerSimulationComplete(
        latitude = 45.4105,
        longitude = 5.2400,
        nomSpot = "Châtaigneraie des Terres Froides (38)",
        topo = topo,
        sol = sol,
        foret = foret,
        meteo = meteo
    )
}

class MainScreenViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(SimulateurUiState())
    val uiState: StateFlow<SimulateurUiState> = _uiState.asStateFlow()

    init {
        simulerPointGps(45.4105, 5.2400, "Châtaigneraie des Terres Froides (38)")
    }

    fun simulerPointGps(latitude: Double, longitude: Double, nomSpot: String? = null) {
        val label = nomSpot ?: String.format("Point GPS (%.4f, %.4f)", latitude, longitude)
        _uiState.update { it.copy(isLoading = true, messageStatut = "Analyse météo, sol & IGN BD Forêt...") }
        viewModelScope.launch {
            try {
                val rapport = ApiEnvironnementMeteo.chargerRapportSpot(latitude, longitude, label)
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        rapport = rapport,
                        especeSelectionnee = null,
                        messageStatut = null
                    )
                }
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        messageStatut = "Mode hors-ligne actif (données locales)"
                    )
                }
            }
        }
    }

    fun changerOnglet(index: Int) {
        _uiState.update { it.copy(ongletActif = index) }
    }

    fun changerJourSelectionne(index: Int) {
        _uiState.update { it.copy(jourSelectionneIndex = index.coerceIn(0, 10)) }
    }

    fun changerRecherche(texte: String) {
        _uiState.update { it.copy(rechercheTexte = texte) }
    }

    fun changerFiltreMode(mode: String) {
        _uiState.update { it.copy(filtreMode = mode) }
    }

    fun selectionnerEspeceDetail(espece: ResultatEspece?) {
        _uiState.update { it.copy(especeSelectionnee = espece) }
    }

    fun ajouterSpotActuelAuxFavoris(nomPersonnalise: String) {
        val r = _uiState.value.rapport
        val descHabitat = when {
            r.foret.enZoneBoisee -> r.foret.peuplements.firstOrNull()?.formationVegetale ?: "Forêt"
            r.foret.enLisiere -> "Prairie en lisière forestière"
            else -> "Prairie / Milieu ouvert"
        }
        val icone = when {
            r.foret.enZoneBoisee -> "🌳"
            r.foret.enLisiere -> "🌿"
            else -> "🌾"
        }
        val nouveau = SpotPredefini(
            nom = nomPersonnalise.ifBlank { "Mon coin (${String.format("%.3f, %.3f", r.latitude, r.longitude)})" },
            region = "Alt. ${r.topographie.altitudeM.toInt()}m • pH ${r.sol.ph}",
            description = "$descHabitat • ${r.topographie.orientation}",
            latitude = r.latitude,
            longitude = r.longitude,
            icone = icone
        )
        _uiState.update { state ->
            state.copy(
                spotsFavoris = listOf(nouveau) + state.spotsFavoris,
                messageStatut = "⭐ Coin enregistré dans vos favoris !"
            )
        }
    }
}
