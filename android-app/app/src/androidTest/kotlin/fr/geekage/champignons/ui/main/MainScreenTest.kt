package fr.geekage.champignons.ui.main

import androidx.compose.ui.test.junit4.createComposeRule
import fr.geekage.champignons.ui.theme.SimulateurChampignonsTheme
import org.junit.Rule
import org.junit.Test

class MainScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun mainScreen_rendersSuccessfully() {
        composeTestRule.setContent {
            SimulateurChampignonsTheme {
                SimulateurChampignonsContent(state = SimulateurUiState())
            }
        }
    }
}
