package com.example.guidewirehomesecurityapp.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.example.guidewirehomesecurityapp.api.EventService
import com.example.guidewirehomesecurityapp.api.SensorEvent
import com.example.guidewirehomesecurityapp.notifications.AlarmFirebaseMessagingService
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun HomeScreen(modifier: Modifier = Modifier) {
    var events by remember { mutableStateOf<List<SensorEvent>>(emptyList()) }
    val lifecycleOwner = LocalLifecycleOwner.current
    val context = LocalContext.current
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* result not needed for FCM registration */ }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= 33) {
            when (ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)) {
                android.content.pm.PackageManager.PERMISSION_GRANTED -> { }
                else -> permissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        // Register FCM token for this device with current user's alarm system (and re-register periodically so it stays correct)
        FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
            if (task.isSuccessful) task.result?.let { AlarmFirebaseMessagingService.registerTokenWithBackend(context, it) }
        }
    }

    LaunchedEffect(lifecycleOwner) {
        var tick = 0
        while (true) {
            events = withContext(Dispatchers.IO) {
                EventService.getEvents(context)
            }
            delay(3000)
            tick++
            // Re-register FCM token every ~30s so this device stays linked to the currently logged-in user's system
            if (tick % 10 == 0) {
                FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                    if (task.isSuccessful) task.result?.let { AlarmFirebaseMessagingService.registerTokenWithBackend(context, it) }
                }
            }
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        if (events.isEmpty()) {
            Text(
                text = "No sensor events yet. Open/close a door on your ESP32 to see events here.",
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.align(Alignment.Center)
            )
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text(
                        text = "Sensor events",
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                }
                items(events.reversed()) { event ->
                    EventCard(event = event)
                }
            }
        }
    }
}

@Composable
private fun EventCard(event: SensorEvent) {
    val timeStr = try {
        val date = Date((event.timestamp * 1000).toLong())
        SimpleDateFormat("MMM d, HH:mm:ss", Locale.getDefault()).format(date)
    } catch (_: Exception) {
        "—"
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = event.displayType(),
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(12.dp)
        )
        Text(
            text = "${event.device_id} · $timeStr",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(start = 12.dp, top = 0.dp, end = 12.dp, bottom = 12.dp),
            fontSize = 12.sp
        )
    }
}
