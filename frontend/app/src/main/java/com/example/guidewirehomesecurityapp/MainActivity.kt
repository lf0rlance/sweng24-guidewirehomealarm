package com.example.guidewirehomesecurityapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import com.example.guidewirehomesecurityapp.ui.screens.*
import com.example.guidewirehomesecurityapp.ui.theme.LogInTheme

class MainActivity : ComponentActivity() {

    sealed class AppScreen {
        object Splash : AppScreen()
        object Login : AppScreen()
        object Home : AppScreen()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            LogInTheme {
                var currentScreen by remember { mutableStateOf<AppScreen>(AppScreen.Splash) }

                when (currentScreen) {
                    AppScreen.Splash -> {
                        SplashScreen { currentScreen = AppScreen.Login }
                    }
                    AppScreen.Login -> {
                        LoginScreen(onLoginSuccess = { currentScreen = AppScreen.Home })
                    }
                    AppScreen.Home -> {
                        HomeScreen(onSignOut = { currentScreen = AppScreen.Login })
                    }
                }
            }
        }
    }
}