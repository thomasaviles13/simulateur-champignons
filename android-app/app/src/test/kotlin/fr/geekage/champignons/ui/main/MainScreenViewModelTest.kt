package fr.geekage.champignons.ui.main

import fr.geekage.champignons.model.ModeleMycologique
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MainScreenViewModelTest {
    @Test
    fun catalogueEspeces_contient80Especes() {
        assertEquals(80, ModeleMycologique.CATALOGUE_ESPECES.size)
    }

    @Test
    fun selectionContextuelle_retourneExactement44Especes() {
        val sel = ModeleMycologique.selectionnerCatalogueContextuel(
            latitude = 45.41,
            longitude = 5.22,
            mois = 11,
            altitude = 410.0,
            essences = listOf("châtaignier", "chêne"),
            nbEspeces = 44
        )
        assertEquals(44, sel.size)
        assertTrue(sel.any { it.id == "bolet_bai" })
        assertTrue(sel.any { it.id == "trompette_mort" })
    }

    @Test
    fun simulationInitiale_retourneEspecesEtStades() {
        val rapport = creerRapportInitialDemo()
        assertTrue(rapport.especesProbables.isNotEmpty())
        val coulemelle = rapport.especesProbables.first { it.espece.id == "coulemelle" }
        assertEquals(100, coulemelle.compatibiliteBiotopePct)
        assertEquals(11, coulemelle.courbeJaJ10.size)
    }
}
