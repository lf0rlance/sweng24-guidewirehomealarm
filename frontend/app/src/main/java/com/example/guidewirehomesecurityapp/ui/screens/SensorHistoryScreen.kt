package com.example.guidewirehomesecurityapp.ui.screens

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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.guidewirehomesecurityapp.api.SensorEvent
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun SensorHistoryScreen(
    modifier: Modifier = Modifier,
    events: List<SensorEvent> = emptyList()
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .padding(20.dp)
    ) {
        if (events.isEmpty()) {
            Text(
                text = "No sensor events yet. Open or close a door on your ESP32 to see history here.",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f),
                modifier = Modifier.align(Alignment.Center)
            )
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text(
                        text = "Sensor activation history",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    Text(
                        text = "Which sensor and whether it was opened or closed.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
                        modifier = Modifier.padding(bottom = 16.dp)
                    )
                }
                items(events.reversed()) { event ->
                    SensorHistoryEventCard(event = event)
                }
            }
        }
    }
}

@Composable
private fun SensorHistoryEventCard(event: SensorEvent) {
    val timeStr = try {
        val date = Date((event.timestamp * 1000).toLong())
        SimpleDateFormat("MMM d, HH:mm:ss", Locale.getDefault()).format(date)
    } catch (_: Exception) {
        "—"
    }
    val openedOrClosed = when (event.event_type) {
        "door_open" -> "Opened"
        "door_closed" -> "Closed"
        else -> event.displayType()
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            text = event.displayType(),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(start = 12.dp, top = 12.dp, end = 12.dp, bottom = 4.dp)
        )
        Text(
            text = "${event.device_id} · $openedOrClosed · $timeStr",
            style = MaterialTheme.typography.bodySmall,
            modifier = Modifier.padding(start = 12.dp, top = 0.dp, end = 12.dp, bottom = 12.dp),
            fontSize = 12.sp,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
