package com.example.guidewirehomesecurityapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.example.guidewirehomesecurityapp.ui.screens.HomeScreen
import com.example.guidewirehomesecurityapp.ui.screens.LoginScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        var isLoggedIn by mutableStateOf(false)

        setContent {
            Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                if (isLoggedIn) {
                    HomeScreen(modifier = Modifier.padding(innerPadding))
                } else {
                    LoginScreen(
                        modifier = Modifier.padding(innerPadding),
                        onLoginSuccess = { isLoggedIn = true }
                    )
                }
            }
        }
    }
}

