package fr.geekage.champignons.model

import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

enum class TypeTrophique(val label: String) {
    MYCORHIZIEN("Mycorhizien"),
    SAPROPHYTE("Saprophyte"),
    LIGNICOLE("Lignicole")
}

enum class ChocThermique {
    BAISSE, HAUSSE, MODERE
}

data class EspeceChampignon(
    val id: String,
    val nom: String,
    val nomScientifique: String,
    val moisActifs: Set<Int>,
    val moisOptimaux: Set<Int>,
    val phMin: Double,
    val phMax: Double,
    val tempSolOptMin: Double,
    val tempSolOptMax: Double,
    val tempSolLimMin: Double,
    val tempSolLimMax: Double,
    val pluie20jOptMin: Double,
    val pluie20jOptMax: Double,
    val delaiMatMin: Int,
    val delaiMatMax: Int,
    val chocThermique: ChocThermique,
    val essencesHotes: List<String>,
    val altitudeMax: Int,
    val typeTrophique: TypeTrophique = TypeTrophique.MYCORHIZIEN,
    val estCryophileGel: Boolean = false
)

data class StadesCarpophore(
    val enPoussePct: Int,
    val adultesPct: Int,
    val vieillissantsPct: Int,
    val icone: String,
    val labelCourt: String,
    val diagnostic: String
)

data class DetailsJour(
    val pluie20jMm: Double,
    val pluieMaturationMm: Double,
    val tempSolC: Double,
    val tminSousBoisC: Double,
    val variationThermiqueC: Double,
    val humiditeSolM3: Double,
    val humiditeAirPct: Double,
    val ventSousBoisKmh: Double,
    val et0SousBoisMm: Double,
    val delaiMaturationJ: Double,
    val vitessePoussePct: Int,
    val joursCroissanceCarpophore: Double?,
    val vitessePousse: String,
    val stadesCarpophore: StadesCarpophore
)

data class ScoreJour(
    val echeance: String,
    val date: String,
    val scorePct: Int,
    val details: DetailsJour
)

data class ResultatEspece(
    val espece: EspeceChampignon,
    val compatibiliteBiotopePct: Int,
    val scoreAujourdhuiPct: Int,
    val scoreMaxJ10Pct: Int,
    val courbeJaJ10: List<ScoreJour>
)

data class ProfilTopographique(
    val altitudeM: Double,
    val penteDeg: Double,
    val pentePct: Double,
    val azimutDeg: Double?,
    val orientation: String,
    val deltaTempSolC: Double,
    val coeffRetentionHumidite: Double,
    val coeffInfiltrationPluie: Double
)

data class ProfilSol(
    val ph: Double,
    val argilePct: Double,
    val sablePct: Double,
    val limonPct: Double,
    val carboneOrganiqueGKg: Double,
    val typeSol: String,
    val source: String
)

data class PeuplementForestier(
    val formationVegetale: String,
    val essence: String,
    val distanceM: Double = 0.0
)

data class ProfilForet(
    val enZoneBoisee: Boolean,
    val enLisiere: Boolean,
    val distanceForetM: Double?,
    val peuplements: List<PeuplementForestier>,
    val peuplementsLisiere: List<PeuplementForestier> = emptyList()
)

data class MicroclimatCanopee(
    val couvert: String,
    val coeffVentSousBois: Double,
    val coeffEt0SousBois: Double,
    val tamponGelC: Double,
    val interceptionBruineRatio: Double,
    val coeffRetentionTexture: Double,
    val coeffInertieMaturation: Double,
    val risqueAsphyxieArgile: Boolean
)

data class SerieMeteo(
    val dates: List<String>,
    val precipitationSum: List<Double>,
    val soilTemperature6cm: List<Double>,
    val soilMoisture0To7cm: List<Double>,
    val temperature2mMin: List<Double>,
    val windSpeed10mMax: List<Double>,
    val et0FaoEvapotranspiration: List<Double>,
    val relativeHumidity2m: List<Double>,
    val indexAujourdHui: Int = 20
)

data class RapportSimulation(
    val latitude: Double,
    val longitude: Double,
    val nomSpot: String,
    val topographie: ProfilTopographique,
    val sol: ProfilSol,
    val foret: ProfilForet,
    val microclimat: MicroclimatCanopee,
    val meteo: SerieMeteo,
    val cumulPluie20jMm: Double,
    val cumulPluiePrevue10jMm: Double,
    val especesProbables: List<ResultatEspece>
)

data class SpotPredefini(
    val nom: String,
    val region: String,
    val description: String,
    val latitude: Double,
    val longitude: Double,
    val icone: String = "🌲"
)

object ModeleMycologique {

    val SPOTS_FAVORIS_DEFAUT = listOf(
        SpotPredefini("Châtaigneraie des Terres Froides", "Isère (38)", "Forêt de châtaigniers sur versant Nord frais (510 m)", 45.4105, 5.2400, "🌰"),
        SpotPredefini("Prairies d'Ornacieux-Balbins", "Isère (38)", "Prairies ouvertes propices aux Marasmes, Rosés et Coulemelles", 45.4021, 5.2231, "🌾"),
        SpotPredefini("Forêt domaniale de Mormal", "Nord (59)", "Hêtraie-chênaie humide à Cèpes, Trompettes et Pieds-de-mouton", 50.2215, 3.7580, "🌳"),
        SpotPredefini("Forêt de Fontainebleau", "Seine-et-Marne (77)", "Chênes, hêtres et pins sur sables acides (Bolets bais, Girolles)", 48.4047, 2.6920, "🌲"),
        SpotPredefini("Landes de Gascogne", "Landes (40)", "Pinède maritime sur sol sableux acide (Cèpes des pins, Lactaires)", 44.1500, -0.8500, "🌲"),
        SpotPredefini("Chaîne des Puys", "Puy-de-Dôme (63)", "Hêtraies-sapinières volcaniques d'altitude (850 m)", 45.7750, 2.9600, "⛰️"),
        SpotPredefini("Massif des Vosges", "Vosges (88)", "Pessières et sapinières moussues (Chanterelles en tube, Cèpes)", 48.0600, 6.8700, "🏔️")
    )

    val CATALOGUE_ESPECES: List<EspeceChampignon> = listOf(
        // --- CÈPES & BOLETS ---
        EspeceChampignon("cepe_bordeaux", "Cèpe de Bordeaux", "Boletus edulis", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.5, 6.5, 8.5, 18.0, 3.5, 23.0, 40.0, 110.0, 7, 14, ChocThermique.BAISSE, listOf("chêne", "hêtre", "châtaignier", "épicéa", "sapin", "pin", "feuillus", "conifères"), 2200),
        EspeceChampignon("cepe_ete", "Cèpe d'été (Réticulé)", "Boletus reticulatus", setOf(5, 6, 7, 8, 9, 10), setOf(6, 7, 8, 9), 5.0, 6.8, 14.0, 22.0, 10.0, 26.0, 35.0, 95.0, 6, 12, ChocThermique.BAISSE, listOf("chêne", "hêtre", "châtaignier", "charme", "feuillus"), 1600),
        EspeceChampignon("cepe_bronze", "Cèpe bronzé (Tête de nègre)", "Boletus aereus", setOf(6, 7, 8, 9, 10), setOf(8, 9, 10), 5.0, 6.8, 14.0, 22.0, 10.0, 26.0, 35.0, 95.0, 8, 15, ChocThermique.BAISSE, listOf("chêne", "châtaignier", "hêtre", "feuillus"), 1200),
        EspeceChampignon("cepe_pins", "Cèpe des pins", "Boletus pinophilus", setOf(5, 6, 7, 8, 9, 10, 11), setOf(9, 10, 11), 4.0, 6.0, 9.0, 17.0, 5.0, 22.0, 40.0, 110.0, 7, 14, ChocThermique.BAISSE, listOf("pin", "sapin", "épicéa", "conifères"), 2000),
        EspeceChampignon("bolet_bai", "Bolet bai", "Imleria badia", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.2, 6.2, 8.0, 17.0, 4.0, 21.0, 35.0, 100.0, 5, 12, ChocThermique.BAISSE, listOf("pin", "épicéa", "sapin", "conifères", "chêne", "hêtre", "châtaignier", "feuillus"), 2000),
        EspeceChampignon("bolet_pied_rouge", "Bolet à pied rouge", "Neoboletus erythropus", setOf(5, 6, 7, 8, 9, 10, 11), setOf(8, 9, 10, 11), 4.2, 6.2, 7.5, 18.0, 3.0, 23.0, 40.0, 110.0, 6, 13, ChocThermique.BAISSE, listOf("hêtre", "chêne", "châtaignier", "épicéa", "sapin", "feuillus", "conifères"), 2200),
        EspeceChampignon("bolet_rude", "Bolet rude (Bouleau)", "Leccinum scabrum", setOf(6, 7, 8, 9, 10, 11), setOf(8, 9, 10), 4.5, 6.5, 7.5, 17.0, 3.0, 22.0, 45.0, 120.0, 6, 12, ChocThermique.BAISSE, listOf("bouleau"), 1800),
        EspeceChampignon("bolet_orange", "Bolet orangé des chênes", "Leccinum aurantiacum", setOf(7, 8, 9, 10, 11), setOf(9, 10), 4.8, 6.8, 8.0, 18.0, 3.5, 22.0, 40.0, 110.0, 7, 14, ChocThermique.BAISSE, listOf("chêne", "peuplier", "tremble", "hêtre", "feuillus"), 1600),
        EspeceChampignon("nonnette_voilee", "Nonnette voilée (Bolet jaune)", "Suillus luteus", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.2, 6.2, 8.0, 16.0, 4.0, 20.0, 35.0, 100.0, 5, 11, ChocThermique.BAISSE, listOf("pin", "conifères"), 2000),
        EspeceChampignon("bolet_mou", "Bolet mou (Bolet des bouviers)", "Suillus bovinus", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.0, 5.8, 7.0, 15.0, 3.0, 19.0, 40.0, 110.0, 5, 11, ChocThermique.BAISSE, listOf("pin", "conifères"), 1800),

        // --- CHANTERELLES, TROMPETTES & HYDNES ---
        EspeceChampignon("girolle", "Girolle (Chanterelle)", "Cantharellus cibarius", setOf(6, 7, 8, 9, 10, 11), setOf(6, 7, 9, 10), 4.5, 6.2, 9.5, 19.0, 5.0, 24.0, 45.0, 120.0, 10, 18, ChocThermique.MODERE, listOf("chêne", "hêtre", "châtaignier", "bouleau", "épicéa", "pin", "feuillus", "conifères"), 2000),
        EspeceChampignon("chanterelle_tube", "Chanterelle en tube (Grise)", "Craterellus tubaeformis", setOf(9, 10, 11, 12), setOf(10, 11, 12), 4.0, 6.0, 5.0, 13.0, 1.0, 17.0, 50.0, 140.0, 7, 15, ChocThermique.BAISSE, listOf("épicéa", "sapin", "pin", "conifères", "hêtre", "chêne", "châtaignier", "feuillus"), 2000, estCryophileGel = true),
        EspeceChampignon("chanterelle_jaunissante", "Chanterelle jaunissante", "Craterellus lutescens", setOf(9, 10, 11, 12), setOf(10, 11), 5.0, 7.2, 6.0, 14.0, 2.0, 18.0, 45.0, 130.0, 7, 15, ChocThermique.BAISSE, listOf("pin", "épicéa", "sapin", "conifères", "hêtre"), 2000, estCryophileGel = true),
        EspeceChampignon("trompette_mort", "Trompette de la mort", "Craterellus cornucopioides", setOf(9, 10, 11, 12), setOf(10, 11), 5.0, 7.2, 7.0, 15.0, 3.0, 19.0, 55.0, 150.0, 8, 16, ChocThermique.BAISSE, listOf("hêtre", "chêne", "charme", "châtaignier", "feuillus"), 1600),
        EspeceChampignon("pied_de_mouton", "Pied-de-mouton", "Hydnum repandum", setOf(9, 10, 11, 12), setOf(10, 11), 4.8, 7.0, 6.0, 14.0, 2.0, 18.0, 45.0, 120.0, 8, 15, ChocThermique.BAISSE, listOf("hêtre", "chêne", "châtaignier", "épicéa", "sapin", "pin", "feuillus", "conifères"), 1800),
        EspeceChampignon("pied_de_mouton_roussissant", "Pied-de-mouton roussissant", "Hydnum rufescens", setOf(9, 10, 11, 12), setOf(10, 11), 4.5, 6.5, 5.0, 13.0, 1.5, 17.0, 45.0, 125.0, 8, 15, ChocThermique.BAISSE, listOf("épicéa", "sapin", "pin", "hêtre", "chêne", "conifères", "feuillus"), 2000, estCryophileGel = true),

        // --- AMANITES COMESTIBLES ---
        EspeceChampignon("amanite_rougissante", "Amanite rougissante (Golmotte)", "Amanita rubescens", setOf(6, 7, 8, 9, 10, 11), setOf(8, 9, 10, 11), 4.2, 6.5, 7.5, 18.0, 3.0, 23.0, 30.0, 105.0, 5, 11, ChocThermique.MODERE, listOf("chêne", "hêtre", "châtaignier", "pin", "épicéa", "sapin", "feuillus", "conifères"), 2000),
        EspeceChampignon("amanite_cesars", "Amanite des Césars (Oronge)", "Amanita caesarea", setOf(7, 8, 9, 10), setOf(8, 9), 5.0, 6.8, 16.0, 24.0, 12.0, 28.0, 30.0, 85.0, 7, 14, ChocThermique.MODERE, listOf("chêne", "châtaignier", "feuillus"), 1000),
        EspeceChampignon("amanite_vaginee", "Amanite vaginée (Grisette)", "Amanita vaginata", setOf(6, 7, 8, 9, 10, 11), setOf(8, 9, 10), 4.5, 6.8, 8.5, 18.0, 4.0, 23.0, 35.0, 100.0, 5, 11, ChocThermique.MODERE, listOf("chêne", "hêtre", "bouleau", "châtaignier", "feuillus", "conifères"), 2000),

        // --- LACCAIRES, POLYPORES & FISTULINES ---
        EspeceChampignon("laccaire_amethyste", "Laccaire améthyste", "Laccaria amethystina", setOf(8, 9, 10, 11, 12), setOf(9, 10, 11), 4.5, 6.8, 6.0, 15.0, 2.0, 20.0, 40.0, 125.0, 5, 11, ChocThermique.BAISSE, listOf("hêtre", "chêne", "châtaignier", "charme", "feuillus", "conifères"), 1800),
        EspeceChampignon("laccaire_laque", "Laccaire laqué", "Laccaria laccata", setOf(6, 7, 8, 9, 10, 11, 12), setOf(9, 10, 11), 4.2, 7.0, 6.0, 16.0, 2.0, 21.0, 35.0, 120.0, 4, 10, ChocThermique.BAISSE, listOf("chêne", "hêtre", "bouleau", "pin", "épicéa", "feuillus", "conifères"), 2200),
        EspeceChampignon("fistuline_hepatique", "Fistuline hépatique (Langue de bœuf)", "Fistulina hepatica", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.5, 6.5, 7.5, 18.0, 3.0, 22.0, 35.0, 105.0, 6, 13, ChocThermique.MODERE, listOf("chêne", "châtaignier", "feuillus"), 1400, TypeTrophique.LIGNICOLE),
        EspeceChampignon("poule_des_bois", "Poule des bois (Maitake)", "Grifola frondosa", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.8, 6.5, 8.0, 18.0, 3.5, 22.0, 40.0, 110.0, 7, 14, ChocThermique.BAISSE, listOf("chêne", "châtaignier", "hêtre", "charme", "feuillus"), 1300, TypeTrophique.LIGNICOLE),
        EspeceChampignon("polypore_soufre", "Polypore soufré", "Laetiporus sulphureus", setOf(5, 6, 7, 8, 9, 10), setOf(5, 6, 9), 5.0, 7.0, 12.0, 21.0, 8.0, 25.0, 35.0, 95.0, 5, 11, ChocThermique.MODERE, listOf("chêne", "robinier", "saule", "peuplier", "châtaignier", "feuillus"), 1500, TypeTrophique.LIGNICOLE),
        EspeceChampignon("sparassis_crepu", "Sparassis crépu (Morille des pins)", "Sparassis crispa", setOf(8, 9, 10, 11), setOf(9, 10, 11), 4.2, 6.2, 7.0, 15.0, 3.0, 19.0, 45.0, 115.0, 7, 14, ChocThermique.BAISSE, listOf("pin", "sapin", "épicéa", "douglas", "conifères"), 1800, TypeTrophique.LIGNICOLE),

        // --- LACTAIRES & RUSSULES ---
        EspeceChampignon("lactaire_delicieux", "Lactaire délicieux (Catalan)", "Lactarius deliciosus", setOf(9, 10, 11, 12), setOf(10, 11), 5.0, 7.5, 8.0, 16.0, 3.0, 20.0, 40.0, 110.0, 6, 13, ChocThermique.BAISSE, listOf("pin", "conifères"), 1800),
        EspeceChampignon("lactaire_sanguin", "Lactaire sanguin", "Lactarius sanguifluus", setOf(9, 10, 11, 12), setOf(10, 11), 6.2, 8.0, 9.0, 17.0, 4.0, 21.0, 35.0, 100.0, 6, 13, ChocThermique.BAISSE, listOf("pin", "conifères"), 1600),
        EspeceChampignon("russule_charbonniere", "Russule charbonnière", "Russula cyanoxantha", setOf(6, 7, 8, 9, 10, 11), setOf(8, 9, 10, 11), 4.5, 6.8, 7.5, 18.0, 3.0, 23.0, 35.0, 105.0, 5, 11, ChocThermique.MODERE, listOf("hêtre", "chêne", "châtaignier", "charme", "feuillus"), 1800),
        EspeceChampignon("russule_verdoyante", "Russule verdoyante (Palomet)", "Russula virescens", setOf(6, 7, 8, 9, 10), setOf(7, 8, 9), 4.8, 6.5, 13.0, 21.0, 9.0, 25.0, 35.0, 95.0, 6, 12, ChocThermique.MODERE, listOf("chêne", "hêtre", "châtaignier", "feuillus"), 1400),
        EspeceChampignon("russule_doree", "Russule dorée", "Russula aurea", setOf(6, 7, 8, 9, 10), setOf(7, 8, 9), 5.0, 7.2, 12.0, 20.0, 8.0, 24.0, 35.0, 95.0, 6, 12, ChocThermique.MODERE, listOf("chêne", "hêtre", "feuillus", "épicéa"), 1600),

        // --- TRICHOLOMES, CLITOCYBES, PIEDS BLEUS & MEUNIERS ---
        EspeceChampignon("pied_bleu", "Pied bleu", "Lepista nuda", setOf(10, 11, 12, 1), setOf(10, 11, 12), 5.0, 7.5, 4.0, 12.0, 1.0, 16.0, 35.0, 100.0, 6, 12, ChocThermique.BAISSE, listOf("chêne", "hêtre", "châtaignier", "feuillus", "épicéa", "pin", "conifères"), 1600, TypeTrophique.SAPROPHYTE, estCryophileGel = true),
        EspeceChampignon("tricholome_terreux", "Tricholome terreux (Petit gris)", "Tricholoma terreum", setOf(9, 10, 11, 12), setOf(10, 11, 12), 6.0, 7.8, 4.0, 13.0, 1.0, 17.0, 35.0, 100.0, 6, 13, ChocThermique.BAISSE, listOf("pin", "épicéa", "sapin", "conifères"), 1800, estCryophileGel = true),
        EspeceChampignon("mousseron_st_georges", "Mousseron de la Saint-Georges", "Calocybe gambosa", setOf(4, 5, 6), setOf(4, 5), 6.2, 7.8, 9.0, 16.0, 5.0, 20.0, 35.0, 90.0, 5, 11, ChocThermique.HAUSSE, listOf("prairie", "lisière", "frêne", "noisetier", "aubépine"), 1600, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("tete_de_moine", "Tête de moine (Clitocybe géotrope)", "Infundibulicybe geotropa", setOf(9, 10, 11, 12), setOf(10, 11), 6.3, 8.0, 5.0, 14.0, 1.5, 18.0, 40.0, 110.0, 7, 14, ChocThermique.BAISSE, listOf("prairie", "lisière", "hêtre", "chêne", "frêne", "sapin"), 1700, TypeTrophique.SAPROPHYTE, estCryophileGel = true),
        EspeceChampignon("meunier", "Meunier (Clitopile petite prune)", "Clitopilus prunulus", setOf(7, 8, 9, 10, 11), setOf(9, 10, 11), 4.5, 6.5, 7.5, 17.0, 3.0, 22.0, 40.0, 110.0, 6, 12, ChocThermique.BAISSE, listOf("chêne", "hêtre", "châtaignier", "épicéa", "feuillus", "conifères"), 1800),

        // --- PLEUROTES, LÉPIOTES, AGARICS, COPRINS & MARASMES ---
        EspeceChampignon("pleurote_huitre", "Pleurote en huître", "Pleurotus ostreatus", setOf(10, 11, 12, 1, 2), setOf(11, 12, 1), 5.2, 7.5, 2.5, 10.0, 0.0, 14.0, 30.0, 95.0, 4, 10, ChocThermique.BAISSE, listOf("hêtre", "peuplier", "saule", "frêne", "charme", "noisetier"), 1500, TypeTrophique.LIGNICOLE, estCryophileGel = true),
        EspeceChampignon("pholiote_peuplier", "Pholiote du peuplier (Pivoulade)", "Cyclocybe cylindracea", setOf(3, 4, 5, 9, 10, 11), setOf(4, 5, 9, 10, 11), 5.5, 7.5, 7.5, 18.0, 3.0, 22.0, 30.0, 90.0, 4, 10, ChocThermique.MODERE, listOf("peuplier", "saule", "orme", "frêne"), 1200, TypeTrophique.LIGNICOLE),
        EspeceChampignon("coulemelle", "Coulemelle (Lépiote élevée)", "Macrolepiota procera", setOf(7, 8, 9, 10, 11), setOf(9, 10, 11), 4.8, 7.2, 7.0, 17.5, 2.5, 22.0, 30.0, 90.0, 5, 10, ChocThermique.MODERE, listOf("chêne", "hêtre", "châtaignier", "feuillus", "pin", "conifères", "prairie"), 1600, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("agaric_bois", "Agaric des bois (Rosé des bois)", "Agaricus sylvicola", setOf(7, 8, 9, 10, 11), setOf(9, 10, 11), 5.0, 7.2, 7.0, 17.0, 2.5, 21.0, 35.0, 95.0, 5, 10, ChocThermique.BAISSE, listOf("hêtre", "chêne", "châtaignier", "épicéa", "sapin", "feuillus", "conifères"), 1700, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("rose_des_pres", "Rosé des prés", "Agaricus campestris", setOf(6, 7, 8, 9, 10, 11), setOf(9, 10, 11), 5.8, 7.5, 7.5, 18.0, 3.0, 22.0, 30.0, 85.0, 4, 9, ChocThermique.BAISSE, listOf("prairie"), 1800, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("coprin_chevelu", "Coprin chevelu", "Coprinus comatus", setOf(5, 6, 9, 10, 11), setOf(9, 10, 11), 5.5, 7.8, 7.0, 15.0, 3.0, 20.0, 30.0, 95.0, 3, 8, ChocThermique.BAISSE, listOf("prairie", "lisière"), 1800, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("marasme_oreades", "Marasme des Oréades (Faux mousseron)", "Marasmius oreades", setOf(5, 6, 7, 8, 9, 10, 11), setOf(6, 9, 10, 11), 5.2, 7.5, 8.0, 19.0, 3.5, 24.0, 30.0, 90.0, 3, 8, ChocThermique.MODERE, listOf("prairie"), 1800, TypeTrophique.SAPROPHYTE),

        // --- MORILLES (PRINTEMPS) ---
        EspeceChampignon("morille_commune", "Morille commune", "Morchella esculenta", setOf(3, 4, 5), setOf(4, 5), 6.2, 8.0, 8.0, 15.0, 5.0, 19.0, 30.0, 85.0, 6, 12, ChocThermique.HAUSSE, listOf("frêne", "orme", "peuplier", "noisetier", "charme", "feuillus", "sapin"), 1800, TypeTrophique.SAPROPHYTE),
        EspeceChampignon("morille_conique", "Morille conique (Morille noire)", "Morchella elata", setOf(3, 4, 5, 6), setOf(4, 5), 5.2, 7.5, 7.0, 14.0, 4.0, 18.0, 35.0, 95.0, 6, 13, ChocThermique.HAUSSE, listOf("sapin", "épicéa", "pin", "conifères", "frêne"), 2200, TypeTrophique.SAPROPHYTE)
    )

    fun scoreIntervalle(valeur: Double?, optMin: Double, optMax: Double, limMin: Double, limMax: Double): Double {
        if (valeur == null) return 0.5
        if (valeur in optMin..optMax) return 1.0
        if (valeur < limMin || valeur > limMax) return 0.0
        return if (valeur < optMin) {
            (valeur - limMin) / max(0.01, optMin - limMin)
        } else {
            (limMax - valeur) / max(0.01, limMax - optMax)
        }
    }

    private fun dureeCroissanceBase(espece: EspeceChampignon): Double {
        return when (espece.id) {
            "coprin_chevelu", "rose_des_pres", "marasme_oreades", "coulemelle", "agaric_bois" -> 2.0
            "girolle", "trompette_mort", "chanterelle_tube", "chanterelle_jaunissante",
            "pied_de_mouton", "pied_de_mouton_roussissant", "poule_des_bois",
            "fistuline_hepatique", "polypore_soufre", "sparassis_crepu" -> 8.0
            else -> 4.0
        }
    }

    private fun persistanceVolee(espece: EspeceChampignon): Int {
        return when (espece.id) {
            "coprin_chevelu", "rose_des_pres" -> 3
            "girolle", "trompette_mort", "chanterelle_tube", "chanterelle_jaunissante",
            "pied_de_mouton", "pied_de_mouton_roussissant", "poule_des_bois",
            "fistuline_hepatique", "polypore_soufre", "sparassis_crepu", "pleurote_huitre" -> 8
            else -> 6
        }
    }

    fun evaluerBiotope(espece: EspeceChampignon, topo: ProfilTopographique, sol: ProfilSol, foret: ProfilForet): Double {
        val scorePh = scoreIntervalle(sol.ph, espece.phMin, espece.phMax, espece.phMin - 0.75, espece.phMax + 0.75)
        val hotes = espece.essencesHotes
        val estPrairialeStricte = hotes.all { it == "prairie" || it == "lisière" }

        val scoreForet = if (foret.peuplements.isEmpty()) {
            if (foret.enLisiere && foret.peuplementsLisiere.isNotEmpty()) {
                val txtLis = foret.peuplementsLisiere.joinToString(" ") { "${it.formationVegetale} ${it.essence}" }.lowercase()
                val corresp = hotes.filter { it != "prairie" && it != "lisière" && txtLis.contains(it) }
                when {
                    hotes.contains("prairie") || hotes.contains("lisière") -> 1.0
                    corresp.isNotEmpty() -> 0.65
                    else -> 0.12
                }
            } else {
                when {
                    hotes.contains("prairie") -> 1.0
                    hotes.contains("lisière") -> 0.65
                    else -> 0.10
                }
            }
        } else {
            val texteForet = foret.peuplements.joinToString(" ") { "${it.formationVegetale} ${it.essence}" }.lowercase()
            val enForetFermee = texteForet.contains("fermée")
            if (estPrairialeStricte) {
                if (enForetFermee) {
                    if (!hotes.contains("lisière")) 0.02 else 0.12
                } else {
                    0.45
                }
            } else {
                val correspondances = hotes.filter { it != "prairie" && it != "lisière" && texteForet.contains(it) }
                val melangeFeuillus = foret.peuplements.any {
                    val fv = it.formationVegetale.lowercase()
                    fv.contains("feuillus") && !fv.contains("pur")
                }
                when {
                    correspondances.any { it != "feuillus" && it != "conifères" } -> 1.0
                    correspondances.isNotEmpty() -> 0.85
                    melangeFeuillus && hotes.any { it in listOf("bouleau", "peuplier", "frêne", "charme", "noisetier", "saule", "orme", "hêtre") } -> 0.45
                    else -> 0.04
                }
            }
        }

        val scoreAlt = if (topo.altitudeM <= espece.altitudeMax) 1.0 else max(0.0, 1.0 - (topo.altitudeM - espece.altitudeMax) / 500.0)
        val scorePente = if (topo.penteDeg <= 22.0) 1.0 else max(0.3, 1.0 - (topo.penteDeg - 22.0) / 30.0)
        val scoreTopo = 0.70 * scoreAlt + 0.30 * scorePente

        val facteurEdaphique = if (espece.typeTrophique == TypeTrophique.LIGNICOLE) {
            0.22 * scorePh + 0.78 * scoreTopo
        } else {
            scorePh * (0.35 + 0.65 * scoreTopo)
        }

        return scoreForet * facteurEdaphique
    }

    fun extraireParametresEdaphiquesEtCanopee(topo: ProfilTopographique, sol: ProfilSol, foret: ProfilForet): MicroclimatCanopee {
        val texteForet = foret.peuplements.joinToString(" ") { it.formationVegetale }.lowercase()
        val (couvert, coeffVent, coeffEt0, tamponGel, interceptionBruine) = when {
            texteForet.contains("fermée") -> listOf("Forêt fermée (canopée dense)", 0.38, 0.58, 2.0, 0.35)
            foret.peuplements.isNotEmpty() -> listOf("Forêt ouverte / Boisement", 0.65, 0.78, 1.0, 0.65)
            foret.enLisiere -> listOf(
                if (foret.distanceForetM != null) "Prairie en lisière (${foret.distanceForetM} m)" else "Prairie en lisière de bois",
                0.78, 0.88, 0.6, 0.90
            )
            else -> listOf("Milieu ouvert / Prairie (Hors forêt)", 1.0, 1.0, 0.0, 1.0)
        }

        val (coeffRetTex, coeffInertie, risqueAsphyxie) = when {
            sol.sablePct >= 55.0 -> Triple(0.90, 0.88, false)
            sol.argilePct >= 30.0 -> Triple(1.12, 1.08, topo.penteDeg < 3.5)
            else -> Triple(1.0, 1.0, false)
        }

        return MicroclimatCanopee(
            couvert = couvert as String,
            coeffVentSousBois = coeffVent as Double,
            coeffEt0SousBois = coeffEt0 as Double,
            tamponGelC = tamponGel as Double,
            interceptionBruineRatio = interceptionBruine as Double,
            coeffRetentionTexture = coeffRetTex,
            coeffInertieMaturation = coeffInertie,
            risqueAsphyxieArgile = risqueAsphyxie
        )
    }

    private fun calculerStadesMaturiteCarpophore(
        precipsEfficaces: List<Double>,
        dDebut: Int,
        delaiCentral: Double,
        dFin: Int,
        coeffAssechementAir: Double,
        facteurGel: Double
    ): StadesCarpophore {
        val persistance = max(2.0, dFin - delaiCentral)
        var sommeJeunes = 0.0
        var sommeAdultes = 0.0
        var sommeVieux = 0.0

        val n = precipsEfficaces.size
        for (i in 0 until n) {
            val pEff = precipsEfficaces[i]
            if (pEff <= 0.1) continue
            val ageJ = (n - 1 - i).toDouble()

            val wJeune = scoreIntervalle(
                ageJ,
                max(1.5, dDebut - 0.3),
                delaiCentral + 0.10 * persistance,
                max(1.0, dDebut - 1.8),
                delaiCentral + 0.42 * persistance
            )
            val wAdulte = scoreIntervalle(
                ageJ,
                delaiCentral + 0.12 * persistance,
                delaiCentral + 0.62 * persistance,
                max(1.5, delaiCentral - 1.0),
                delaiCentral + 0.90 * persistance
            )
            val wVieux = scoreIntervalle(
                ageJ,
                delaiCentral + 0.68 * persistance,
                dFin + 0.8,
                delaiCentral + 0.38 * persistance,
                min(22.0, dFin + 3.2)
            )

            sommeJeunes += pEff * wJeune
            sommeAdultes += pEff * wAdulte
            sommeVieux += pEff * wVieux
        }

        if (coeffAssechementAir < 0.55 && sommeAdultes > 0) {
            val transfert = sommeAdultes * (0.55 - coeffAssechementAir) * 0.75
            sommeAdultes = max(0.0, sommeAdultes - transfert)
            sommeVieux += transfert
        }
        if (facteurGel < 0.60 && sommeAdultes > 0) {
            val transfert = sommeAdultes * 0.45
            sommeAdultes = max(0.0, sommeAdultes - transfert)
            sommeVieux += transfert
        }

        val total = sommeJeunes + sommeAdultes + sommeVieux
        if (total <= 0.25) {
            return StadesCarpophore(0, 0, 0, "—", "Aucune volée active", "Aucune volée active")
        }

        val pctJ = ((100.0 * sommeJeunes) / total).roundToInt()
        val pctA = ((100.0 * sommeAdultes) / total).roundToInt()
        val pctV = max(0, 100 - pctJ - pctA)

        val seuil = 24
        val (icone, label) = when {
            pctJ >= seuil && pctA >= seuil && pctV >= seuil -> "🌱🍄🍂" to "En pousse, Adultes & Vieillissants"
            pctJ >= 58 -> "🌱" to "En pousse (jeunes)"
            pctA >= 58 -> "🍄" to "Adultes (pleine maturité)"
            pctV >= 58 -> "🍂" to "Vieillissants (fin de volée)"
            pctJ >= seuil && pctA >= seuil -> "🌱🍄" to "En pousse & Adultes"
            pctA >= seuil && pctV >= seuil -> "🍄🍂" to "Adultes & Vieillissants"
            pctJ >= seuil && pctV >= seuil -> "🌱🍂" to "Double volée (En pousse & Vieillissants)"
            pctJ >= pctA && pctJ >= pctV -> "🌱" to "En pousse (jeunes)"
            pctA >= pctJ && pctA >= pctV -> "🍄" to "Adultes (pleine maturité)"
            else -> "🍂" to "Vieillissants (fin de volée)"
        }

        return StadesCarpophore(
            enPoussePct = pctJ,
            adultesPct = pctA,
            vieillissantsPct = pctV,
            icone = icone,
            labelCourt = label,
            diagnostic = "$icone $label ($pctJ% en pousse • $pctA% adultes • $pctV% vieillissants)"
        )
    }

    fun calculerScoreJour(
        espece: EspeceChampignon,
        meteo: SerieMeteo,
        indexJour: Int,
        echeanceLabel: String,
        scoreBiotope: Double,
        topo: ProfilTopographique,
        paramsEco: MicroclimatCanopee
    ): ScoreJour {
        val dateStr = meteo.dates[indexJour]
        val mois = dateStr.substring(5, 7).toIntOrNull() ?: 10
        val bonusHumusAutomne = if (mois in setOf(10, 11, 12, 1, 2, 3)) max(0.8, paramsEco.tamponGelC * 1.05) else 0.0
        val coeffRetHum = topo.coeffRetentionHumidite * paramsEco.coeffRetentionTexture

        val serieTempSol = meteo.soilTemperature6cm.map { round1(it + topo.deltaTempSolC + bonusHumusAutomne) }
        val humiditesSol = meteo.soilMoisture0To7cm.map { round3(it * coeffRetHum) }

        val facteurSaison = when (mois) {
            in espece.moisOptimaux -> 1.0
            in espece.moisActifs -> 0.75
            else -> 0.0
        }

        val debut3j = max(0, indexJour - 2)
        val ventEffectif = round1(meteo.windSpeed10mMax.subList(debut3j, indexJour + 1).average() * paramsEco.coeffVentSousBois)
        val et0Effectif = round1(meteo.et0FaoEvapotranspiration.subList(debut3j, indexJour + 1).average() * paramsEco.coeffEt0SousBois)
        val hrMoy = round1(meteo.relativeHumidity2m.subList(debut3j, indexJour + 1).average())

        val scoreVent = scoreIntervalle(ventEffectif, 0.0, 14.0, 0.0, 38.0)
        val scoreEt0 = scoreIntervalle(et0Effectif, 0.0, 1.8, 0.0, 4.5)
        val scoreHrAir = scoreIntervalle(hrMoy, 75.0, 100.0, 42.0, 100.0)
        val coeffAssechementAir = 0.40 * scoreHrAir + 0.35 * scoreVent + 0.25 * scoreEt0

        // Cinétique dynamique d'incubation et de pousse
        val debut12j = max(0, indexJour - 12)
        val tIncub = serieTempSol.subList(debut12j, indexJour + 1).average()
        val hIncub = humiditesSol.subList(debut12j, indexJour + 1).average()

        val ratioTempIncub = when {
            tIncub >= espece.tempSolOptMax -> 1.0
            tIncub <= espece.tempSolLimMin -> 0.0
            else -> (tIncub - espece.tempSolLimMin) / max(0.5, espece.tempSolOptMax - espece.tempSolLimMin)
        }
        val ratioHumIncub = scoreIntervalle(hIncub, 0.24, 0.42, 0.10, 0.55)
        val ratioVitesseIncub = ratioTempIncub * (0.35 + 0.65 * ratioHumIncub)

        val dMin = espece.delaiMatMin.toDouble()
        val dMax = espece.delaiMatMax.toDouble()
        val delaiCentral = (dMax - ratioVitesseIncub * (dMax - dMin)) * paramsEco.coeffInertieMaturation
        val delaiCentralClamp = delaiCentral.coerceIn(2.0, 20.0)
        val margeAvant = max(2.0, (dMax - dMin) * 0.45)
        val persistanceJ = persistanceVolee(espece)
        val dDebut = max(2.0, delaiCentralClamp - margeAvant).roundToInt()
        val dFin = min(20.0, delaiCentralClamp + persistanceJ).roundToInt()

        val tActuel = serieTempSol.subList(debut3j, indexJour + 1).average()
        val hActuel = humiditesSol.subList(debut3j, indexJour + 1).average()
        val coeffTempPousse = scoreIntervalle(tActuel, espece.tempSolOptMin, espece.tempSolOptMax, espece.tempSolLimMin, espece.tempSolLimMax)
        val coeffHumPousse = scoreIntervalle(hActuel, 0.22, 0.42, 0.11, 0.55)
        val vitesseRel = min(1.0, coeffTempPousse * coeffHumPousse * max(0.30, coeffAssechementAir))
        val dureeBase = dureeCroissanceBase(espece)

        val (joursCroissance, qualifVitesse) = when {
            facteurSaison == 0.0 -> null to "Hors saison"
            coeffTempPousse < 0.08 -> null to "Bloquée (froid/chaud)"
            coeffHumPousse < 0.10 || coeffAssechementAir < 0.25 -> null to "Bloquée (sécheresse/vent)"
            else -> {
                val jc = round1(dureeBase / max(0.20, vitesseRel))
                val q = when {
                    vitesseRel >= 0.80 -> "Rapide (~$jc j)"
                    vitesseRel >= 0.45 -> "Modérée (~$jc j)"
                    else -> "Ralentie (~$jc j)"
                }
                jc to q
            }
        }

        // Précipitations efficaces sur 20 jours
        fun pluieEfficace(pBrute: Double): Double {
            if (pBrute <= 0.0) return 0.0
            val pFiltree = when {
                pBrute < 2.0 -> pBrute * paramsEco.interceptionBruineRatio
                paramsEco.interceptionBruineRatio < 0.5 -> pBrute * 0.88
                else -> pBrute
            }
            return pFiltree * topo.coeffInfiltrationPluie
        }

        val debut20j = max(0, indexJour - 20)
        val fenetrePluie = (debut20j..indexJour).map { pluieEfficace(meteo.precipitationSum[it]) }
        val cumul20j = round1(fenetrePluie.sum())

        val picDebut = max(1.5, delaiCentralClamp - 1.0)
        val picFin = delaiCentralClamp + 0.45 * max(1.0, dFin - delaiCentralClamp)
        val ageMin = max(1.0, dDebut - 1.5)
        val ageMax = min(21.0, dFin + 2.0)

        var pluieMaturation = 0.0
        for (idxP in debut20j..indexJour) {
            val ageJ = (indexJour - idxP).toDouble()
            val poids = when {
                ageJ < ageMin || ageJ > ageMax -> 0.0
                ageJ in picDebut..picFin -> 1.0
                ageJ < picDebut -> (ageJ - ageMin) / max(0.5, picDebut - ageMin)
                else -> (ageMax - ageJ) / max(0.5, ageMax - picFin)
            }
            if (poids > 0.0) {
                pluieMaturation += pluieEfficace(meteo.precipitationSum[idxP]) * poids
            }
        }
        pluieMaturation = round1(pluieMaturation)

        val idxMatDebut = max(0, indexJour - dFin)
        val idxMatFin = max(1, indexJour - dDebut + 1)
        val cumulAvantEmergence = round1((debut20j until idxMatFin).sumOf { pluieEfficace(meteo.precipitationSum[it]) })

        val scoreCumul20j = scoreIntervalle(cumulAvantEmergence, espece.pluie20jOptMin * 0.70, espece.pluie20jOptMax, 4.0, espece.pluie20jOptMax + 90.0)
        val scoreMaturation = scoreIntervalle(pluieMaturation, espece.pluie20jOptMin * 0.42, espece.pluie20jOptMax * 0.80, 1.5, espece.pluie20jOptMax * 1.15)

        val pluieAvantInduction = (debut20j until idxMatDebut).sumOf { pluieEfficace(meteo.precipitationSum[it]) }
        val bonusReveil = when {
            pluieAvantInduction < 12.0 && pluieMaturation >= espece.pluie20jOptMin * 0.40 -> 1.12
            paramsEco.risqueAsphyxieArgile && cumul20j > 135.0 -> 0.72
            else -> 1.0
        }

        val scorePluie = min(1.0, (0.42 * scoreCumul20j + 0.58 * scoreMaturation) * bonusReveil)
        val scoreHumSol = scoreIntervalle(hActuel, 0.22, 0.42, 0.09, 0.55)
        val scoreHumidite = 0.75 * scoreHumSol + 0.25 * coeffAssechementAir
        val scoreHydrique = if (scorePluie < 0.25) scorePluie * (0.35 + 0.65 * scoreHumidite) else (0.58 * scorePluie + 0.42 * scoreHumidite)

        // Température du sol (65% incubation 12j + 35% maintien 3j)
        val tSol = round1(0.65 * tIncub + 0.35 * tActuel)
        val scoreTemp = scoreIntervalle(tSol, espece.tempSolOptMin, espece.tempSolOptMax, espece.tempSolLimMin, espece.tempSolLimMax)

        val tminSousBois = round1(
            meteo.temperature2mMin.subList(debut3j, indexJour + 1).minOf { it + paramsEco.tamponGelC + topo.deltaTempSolC * 0.5 }
        )
        val facteurGel = if (espece.estCryophileGel) {
            when {
                tminSousBois in -2.5..2.0 -> 1.12
                tminSousBois < -5.0 -> 0.25
                else -> 1.0
            }
        } else {
            when {
                tminSousBois <= -3.0 -> 0.08
                tminSousBois <= -1.0 -> 0.42
                else -> 1.0
            }
        }

        val idxChoc1 = max(0, indexJour - dFin - 4)
        val idxChoc2 = max(1, indexJour - dDebut)
        val avantChoc = serieTempSol.subList(idxChoc1, max(idxChoc1 + 1, idxChoc2)).average()
        val apresChoc = serieTempSol.subList(idxChoc2, max(idxChoc2 + 1, indexJour)).average()
        val deltaTemp = round1(apresChoc - avantChoc)

        val bonusChoc = when (espece.chocThermique) {
            ChocThermique.BAISSE -> when {
                deltaTemp in -6.5..-1.2 -> 1.0
                deltaTemp < -6.5 -> 0.80
                deltaTemp > 2.5 -> 0.55
                else -> 0.75
            }
            ChocThermique.HAUSSE -> when {
                deltaTemp in 1.2..6.5 -> 1.0
                deltaTemp < -2.0 -> 0.50
                else -> 0.75
            }
            ChocThermique.MODERE -> 0.75
        }

        val scoreThermique = min(1.0, scoreTemp * (0.78 + 0.22 * bonusChoc) * facteurGel)
        val facteurDessiccation = 0.35 + 0.65 * min(1.0, coeffAssechementAir * 1.25)
        val facteurLimEau = min(1.0, scoreHydrique * 1.45) * facteurDessiccation
        val facteurLimTemp = min(1.0, scoreTemp * 1.45) * min(1.0, facteurGel)

        val scoreFinal = 100.0 * facteurSaison * scoreBiotope * facteurLimEau * facteurLimTemp * (0.52 * scoreHydrique + 0.48 * scoreThermique)
        val scorePct = scoreFinal.roundToInt().coerceIn(0, 100)

        val stades = calculerStadesMaturiteCarpophore(
            precipsEfficaces = fenetrePluie,
            dDebut = dDebut,
            delaiCentral = delaiCentralClamp,
            dFin = dFin,
            coeffAssechementAir = coeffAssechementAir,
            facteurGel = facteurGel
        )

        return ScoreJour(
            echeance = echeanceLabel,
            date = dateStr,
            scorePct = scorePct,
            details = DetailsJour(
                pluie20jMm = cumul20j,
                pluieMaturationMm = pluieMaturation,
                tempSolC = tSol,
                tminSousBoisC = tminSousBois,
                variationThermiqueC = deltaTemp,
                humiditeSolM3 = round3(hActuel),
                humiditeAirPct = hrMoy,
                ventSousBoisKmh = ventEffectif,
                et0SousBoisMm = et0Effectif,
                delaiMaturationJ = round1(delaiCentralClamp),
                vitessePoussePct = (vitesseRel * 100).roundToInt(),
                joursCroissanceCarpophore = joursCroissance,
                vitessePousse = qualifVitesse,
                stadesCarpophore = stades
            )
        )
    }

    fun executerSimulationComplete(
        latitude: Double,
        longitude: Double,
        nomSpot: String,
        topo: ProfilTopographique,
        sol: ProfilSol,
        foret: ProfilForet,
        meteo: SerieMeteo
    ): RapportSimulation {
        val microclimat = extraireParametresEdaphiquesEtCanopee(topo, sol, foret)
        val idxJ = meteo.indexAujourdHui
        val indicesSimulation = (idxJ until min(meteo.dates.size, idxJ + 11)).toList()
        val moisPeriode = indicesSimulation.mapNotNull { meteo.dates[it].substring(5, 7).toIntOrNull() }.toSet()

        val resultats = CATALOGUE_ESPECES
            .filter { esp -> esp.moisActifs.intersect(moisPeriode).isNotEmpty() }
            .map { esp ->
                val biotope = evaluerBiotope(esp, topo, sol, foret)
                val courbe = indicesSimulation.mapIndexed { k, idx ->
                    val ech = if (k == 0) "J" else "J+$k"
                    calculerScoreJour(esp, meteo, idx, ech, biotope, topo, microclimat)
                }
                val scoreJ = courbe.firstOrNull()?.scorePct ?: 0
                val scoreMax = courbe.maxOfOrNull { it.scorePct } ?: 0
                ResultatEspece(
                    espece = esp,
                    compatibiliteBiotopePct = (biotope * 100.0).roundToInt(),
                    scoreAujourdhuiPct = scoreJ,
                    scoreMaxJ10Pct = scoreMax,
                    courbeJaJ10 = courbe
                )
            }
            .sortedWith(compareByDescending<ResultatEspece> { it.scoreMaxJ10Pct }.thenByDescending { it.scoreAujourdhuiPct })

        val cumul20j = round1(meteo.precipitationSum.subList(0, min(meteo.precipitationSum.size, idxJ + 1)).sum())
        val cumul10j = round1(meteo.precipitationSum.subList(min(meteo.precipitationSum.size, idxJ + 1), meteo.precipitationSum.size).sum())

        return RapportSimulation(
            latitude = latitude,
            longitude = longitude,
            nomSpot = nomSpot,
            topographie = topo,
            sol = sol,
            foret = foret,
            microclimat = microclimat,
            meteo = meteo,
            cumulPluie20jMm = cumul20j,
            cumulPluiePrevue10jMm = cumul10j,
            especesProbables = resultats
        )
    }

    private fun round1(v: Double): Double = (v * 10.0).roundToInt() / 10.0
    private fun round3(v: Double): Double = (v * 1000.0).roundToInt() / 1000.0
}
