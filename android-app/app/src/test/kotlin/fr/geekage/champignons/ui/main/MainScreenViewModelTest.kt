package fr.geekage.champignons.ui.main

import fr.geekage.champignons.model.ModeleMycologique
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MainScreenViewModelTest {
    @Test
    fun catalogueEspeces_contient42Especes() {
        assertEquals(42, ModeleMycologique.CATALOGUE_ESPECES.size)
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
