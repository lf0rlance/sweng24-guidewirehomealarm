package com.example.guidewirehomesecurityapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.example.guidewirehomesecurityapp.ui.screens.HomeScreen
import com.example.guidewirehomesecurityapp.ui.screens.LoginScreen
import com.example.guidewirehomesecurityapp.ui.screens.SplashScreen
import com.example.guidewirehomesecurityapp.ui.theme.LogInTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        var showSplash by mutableStateOf(true)
        var isLoggedIn by mutableStateOf(false)

        setContent {
            LogInTheme {
                AnimatedContent(
                    targetState = when {
                        showSplash -> 0
                        !isLoggedIn -> 1
                        else -> 2
                    },
                    transitionSpec = {
                        fadeIn(animationSpec = tween(280)) togetherWith
                            fadeOut(animationSpec = tween(280))
                    },
                    label = "app_screen_transition"
                ) { state ->
                    when (state) {
                        0 -> SplashScreen(onSplashFinished = { showSplash = false })
                        1 -> Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                            LoginScreen(
                                modifier = Modifier.padding(innerPadding),
                                onLoginSuccess = { isLoggedIn = true }
                            )
                        }
                        else -> Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                            HomeScreen(
                                modifier = Modifier.padding(innerPadding),
                                onSignOut = { isLoggedIn = false }
                            )
                        }
                    }
                }
            }
        }
    }
}
