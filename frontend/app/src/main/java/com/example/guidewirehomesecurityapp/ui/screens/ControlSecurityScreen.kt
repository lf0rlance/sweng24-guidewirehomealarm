package com.example.guidewirehomesecurityapp.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.guidewirehomesecurityapp.api.AlarmService
import com.example.guidewirehomesecurityapp.api.EventService
import com.example.guidewirehomesecurityapp.api.SensorEvent
import com.example.guidewirehomesecurityapp.ui.components.ScreenTitleWithLogo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Latest open/closed state for reed 1 and reed 2 from events (newest timestamp wins). */
private fun deriveOpenStates(events: List<SensorEvent>): Pair<Boolean?, Boolean?> {
    var s1: Boolean? = null
    var s2: Boolean? = null
    for (e in events.sortedByDescending { it.timestamp }) {
        when (e.event_type) {
            "door_open" -> if (s1 == null) s1 = true
            "door_closed" -> if (s1 == null) s1 = false
            "door_open_2" -> if (s2 == null) s2 = true
            "door_closed_2" -> if (s2 == null) s2 = false
        }
        if (s1 != null && s2 != null) break
    }
    return Pair(s1, s2)
}

@Composable
fun ControlSecurityScreen(
    modifier: Modifier = Modifier,
    events: List<SensorEvent> = emptyList(),
) {
    val context = LocalContext.current
    var systemArmed by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(true) }
    var labels by remember { mutableStateOf<List<String>>(emptyList()) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        loading = true
        val armed = withContext(Dispatchers.IO) { AlarmService.getArmedStatus(context) }
        if (armed != null) systemArmed = armed
        labels = withContext(Dispatchers.IO) { EventService.getSensorLabels(context) }
        loading = false
    }

    val (open1, open2) = remember(events) { deriveOpenStates(events) }
    val name1 = labels.getOrNull(0)?.takeIf { it.isNotBlank() } ?: "Sensor 1"
    val name2 = labels.getOrNull(1)?.takeIf { it.isNotBlank() } ?: "Sensor 2"

    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .padding(20.dp)
            .verticalScroll(scrollState)
    ) {
        ScreenTitleWithLogo(
            title = "System control",
            modifier = Modifier.padding(bottom = 8.dp),
            style = MaterialTheme.typography.headlineMedium
        )
        Text(
            text = "Arm or disarm the alarm and check sensor status. Names are set by your administrator.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
            modifier = Modifier.padding(bottom = 24.dp)
        )

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
            shape = CardDefaults.elevatedShape
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Alarm system",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onPrimaryContainer
                    )
                    Text(
                        text = if (systemArmed) "Armed" else "Disarmed",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                    )
                }
                Switch(
                    checked = systemArmed,
                    onCheckedChange = { newValue ->
                        systemArmed = newValue
                        scope.launch {
                            val ok = withContext(Dispatchers.IO) {
                                AlarmService.setArmedStatus(context, newValue)
                            }
                            if (!ok) systemArmed = !newValue
                        }
                    },
                    enabled = !loading,
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = MaterialTheme.colorScheme.primary,
                        checkedTrackColor = MaterialTheme.colorScheme.secondaryContainer
                    )
                )
            }
        }

        Spacer(Modifier.height(24.dp))
        Text(
            text = "Sensors",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        listOf(
            Triple(name1, open1, "First reed (GPIO 4)"),
            Triple(name2, open2, "Second reed (GPIO 14)"),
        ).forEach { (name, isOpen, hint) ->
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = name,
                            style = MaterialTheme.typography.bodyLarge,
                            fontWeight = FontWeight.Medium,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = when (isOpen) {
                                true -> "Open"
                                false -> "Closed"
                                null -> "—"
                            },
                            style = MaterialTheme.typography.labelLarge,
                            color = when (isOpen) {
                                true -> MaterialTheme.colorScheme.error
                                false -> MaterialTheme.colorScheme.primary
                                null -> MaterialTheme.colorScheme.onSurfaceVariant
                            }
                        )
                    }
                    Text(
                        text = hint,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }
    }
}
