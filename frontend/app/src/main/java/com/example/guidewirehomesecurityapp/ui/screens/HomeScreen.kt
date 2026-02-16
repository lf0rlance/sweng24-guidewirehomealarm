package com.example.guidewirehomesecurityapp.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.core.content.ContextCompat
import com.example.guidewirehomesecurityapp.api.EventService
import com.example.guidewirehomesecurityapp.api.SensorEvent
import com.example.guidewirehomesecurityapp.notifications.AlarmFirebaseMessagingService
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

sealed class HomeTab(val title: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    data object Home : HomeTab("Home", Icons.Filled.Home)
    data object Control : HomeTab("Control", Icons.Filled.Lock)
    data object History : HomeTab("History", Icons.Filled.History)
    data object Eco : HomeTab("Eco", Icons.Filled.Eco)
    data object Settings : HomeTab("Settings", Icons.Filled.Settings)
}

private val homeTabs = listOf(
    HomeTab.Home,
    HomeTab.Control,
    HomeTab.History,
    HomeTab.Eco,
    HomeTab.Settings
)

@Composable
fun HomeScreen(
    modifier: Modifier = Modifier,
    onSignOut: () -> Unit = {}
) {
    var selectedIndex by rememberSaveable { mutableIntStateOf(0) }
    var events by mutableStateOf<List<SensorEvent>>(emptyList())
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= 33) {
            when (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)) {
                android.content.pm.PackageManager.PERMISSION_GRANTED -> { }
                else -> permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) task.result?.let {
                AlarmFirebaseMessagingService.registerTokenWithBackend(context, it)
            }
        }
    }

    LaunchedEffect(lifecycleOwner) {
        var tick = 0
        while (true) {
            events = withContext(Dispatchers.IO) { EventService.getEvents(context) }
            delay(3000)
            tick++
            if (tick % 10 == 0) {
                FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                    if (task.isSuccessful) task.result?.let {
                        AlarmFirebaseMessagingService.registerTokenWithBackend(context, it)
                    }
                }
            }
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar {
                homeTabs.forEachIndexed { index, tab ->
                    NavigationBarItem(
                        selected = selectedIndex == index,
                        onClick = { selectedIndex = index },
                        icon = { Icon(imageVector = tab.icon, contentDescription = tab.title) },
                        label = { Text(tab.title) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = MaterialTheme.colorScheme.onPrimaryContainer,
                            selectedTextColor = MaterialTheme.colorScheme.onPrimaryContainer,
                            unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                            unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                            indicatorColor = MaterialTheme.colorScheme.primaryContainer
                        )
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(
                    brush = Brush.linearGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f),
                            MaterialTheme.colorScheme.secondaryContainer.copy(alpha = 0.35f),
                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.25f)
                        ),
                        start = Offset(0f, 0f),
                        end = Offset(1000f, 1200f)
                    )
                )
        ) {
            AnimatedContent(
                targetState = selectedIndex,
                transitionSpec = {
                    fadeIn(animationSpec = tween(220)) togetherWith
                        fadeOut(animationSpec = tween(220))
                },
                label = "tab_transition"
            ) { index ->
                when (homeTabs[index]) {
                    HomeTab.Home -> HomeDashboardScreen(
                        modifier = Modifier.padding(innerPadding),
                        recentEvents = events,
                        onNavigateToControl = { selectedIndex = homeTabs.indexOf(HomeTab.Control) },
                        onNavigateToHistory = { selectedIndex = homeTabs.indexOf(HomeTab.History) },
                        onNavigateToSustainability = { selectedIndex = homeTabs.indexOf(HomeTab.Eco) },
                        onNavigateToSettings = { selectedIndex = homeTabs.indexOf(HomeTab.Settings) }
                    )
                    HomeTab.Control -> ControlSecurityScreen(modifier = Modifier.padding(innerPadding))
                    HomeTab.History -> SensorHistoryScreen(
                        modifier = Modifier.padding(innerPadding),
                        events = events
                    )
                    HomeTab.Eco -> SustainabilityScreen(modifier = Modifier.padding(innerPadding))
                    HomeTab.Settings -> SettingsScreen(
                        modifier = Modifier.padding(innerPadding),
                        onSignOut = onSignOut
                    )
                }
            }
        }
    }
}
