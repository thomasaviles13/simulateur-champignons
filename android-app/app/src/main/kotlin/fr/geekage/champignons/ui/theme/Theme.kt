package fr.geekage.champignons.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val ForestDarkColorScheme = darkColorScheme(
    primary = primaryDark,
    onPrimary = Color(0xFF052E16),
    primaryContainer = primaryContainerDark,
    onPrimaryContainer = Color(0xFFBBF7D0),
    secondary = secondaryDark,
    tertiary = tertiaryDark,
    background = backgroundDark,
    onBackground = Color(0xFFE7F3EA),
    surface = surfaceDark,
    onSurface = Color(0xFFE7F3EA),
    surfaceVariant = Color(0xFF1F3326),
    onSurfaceVariant = Color(0xFF94AD9C),
)

@Composable
fun SimulateurChampignonsTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = ForestDarkColorScheme,
        typography = Typography,
        content = content
    )
}
