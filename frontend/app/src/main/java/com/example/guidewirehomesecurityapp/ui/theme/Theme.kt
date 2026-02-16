package com.example.guidewirehomesecurityapp.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// Guidewire Home Security brand colours: light red and light blue
private val LightRed = Color(0xFFE8B4B8)
private val LightRedDark = Color(0xFFD4959A)
private val LightBlue = Color(0xFFB4D4E8)
private val LightBlueDark = Color(0xFF7BB3D4)
private val LightYellowAccent = Color(0xFFF5E6B3)

private val LightColorScheme = lightColorScheme(
    primary = LightBlueDark,
    onPrimary = Color.White,
    primaryContainer = LightBlue,
    onPrimaryContainer = Color(0xFF1A3A4D),
    secondary = LightRedDark,
    onSecondary = Color.White,
    secondaryContainer = LightRed,
    onSecondaryContainer = Color(0xFF4A2528),
    tertiary = LightYellowAccent,
    background = Color(0xFFF8FAFC),
    onBackground = Color(0xFF1A1C1E),
    surface = Color.White,
    onSurface = Color(0xFF1A1C1E)
)

private val DarkColorScheme = darkColorScheme(
    primary = LightBlue,
    onPrimary = Color(0xFF1A3A4D),
    primaryContainer = LightBlueDark,
    onPrimaryContainer = Color.White,
    secondary = LightRed,
    onSecondary = Color(0xFF4A2528),
    secondaryContainer = LightRedDark,
    onSecondaryContainer = Color.White,
    tertiary = LightYellowAccent,
    background = Color(0xFF1A1C1E),
    onBackground = Color(0xFFE3E2E6),
    surface = Color(0xFF1A1C1E),
    onSurface = Color(0xFFE3E2E6)
)

@Composable
fun LogInTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }
    MaterialTheme(
        colorScheme = colorScheme,
        content = content
    )
}
