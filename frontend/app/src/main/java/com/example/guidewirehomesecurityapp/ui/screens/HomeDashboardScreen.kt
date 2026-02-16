package com.example.guidewirehomesecurityapp.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Eco
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.People
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.guidewirehomesecurityapp.api.SensorEvent
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private const val CARD_HEIGHT_DP = 172

@Composable
fun HomeDashboardScreen(
    modifier: Modifier = Modifier,
    recentEvents: List<SensorEvent> = emptyList(),
    onNavigateToControl: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSustainability: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    val reversed = recentEvents.reversed()
    val previewEvents = reversed.take(2)

    val cards = listOf(
        DashboardPreviewItem(
            title = "Control system",
            icon = Icons.Filled.Lock,
            onClick = onNavigateToControl,
            previewContent = {
                Text("Alarm: Disarmed", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("Front door: Closed", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        ),
        DashboardPreviewItem(
            title = "Sensor history",
            icon = Icons.Filled.History,
            onClick = onNavigateToHistory,
            previewContent = {
                if (previewEvents.isEmpty()) {
                    Text("No recent events", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                } else {
                    previewEvents.forEach { event ->
                        val timeStr = try {
                            SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date((event.timestamp * 1000).toLong()))
                        } catch (_: Exception) { "—" }
                        Text("${event.displayType()} · $timeStr", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                }
            }
        ),
        DashboardPreviewItem(
            title = "Eco",
            icon = Icons.Filled.Eco,
            onClick = onNavigateToSustainability,
            previewContent = {
                Text("~2.4 kWh saved", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("~1.2 kg CO₂e reduced", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        ),
        DashboardPreviewItem(
            title = "Manage authorised users",
            icon = Icons.Filled.People,
            onClick = onNavigateToSettings,
            previewContent = {
                Text("Add or view users", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text("Permissions & roles", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
        )
    )

    Column(modifier = modifier.padding(20.dp)) {
        Text(
            text = "Guidewire Home Security App",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(bottom = 6.dp)
        )
        Text(
            text = "Keeping your home safe and secure",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.85f),
            modifier = Modifier.padding(bottom = 24.dp)
        )
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(0.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(cards) { card ->
                DashboardCard(
                    title = card.title,
                    icon = card.icon,
                    previewContent = card.previewContent,
                    onClick = card.onClick
                )
            }
        }
    }
}

private data class DashboardPreviewItem(
    val title: String,
    val icon: androidx.compose.ui.graphics.vector.ImageVector,
    val previewContent: @Composable () -> Unit,
    val onClick: () -> Unit
)

@Composable
private fun DashboardCard(
    title: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    previewContent: @Composable () -> Unit,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .height(CARD_HEIGHT_DP.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.92f)
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                modifier = Modifier.size(28.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                previewContent()
            }
        }
    }
}
