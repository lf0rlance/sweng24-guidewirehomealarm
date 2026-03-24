package com.example.guidewirehomesecurityapp.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.guidewirehomesecurityapp.api.EventService
import com.example.guidewirehomesecurityapp.notifications.AlarmFirebaseMessagingService
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import androidx.compose.runtime.rememberCoroutineScope
import com.example.guidewirehomesecurityapp.ui.components.ScreenTitleWithLogo

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    onSignOut: () -> Unit = {}
) {
    val scrollState = rememberScrollState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    Column(
        modifier = modifier
            .padding(20.dp)
            .verticalScroll(scrollState)
    ) {
        ScreenTitleWithLogo(
            title = "Settings",
            modifier = Modifier.padding(bottom = 8.dp),
            style = MaterialTheme.typography.headlineMedium
        )
        Text(
            text = "Account and app preferences",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f),
            modifier = Modifier.padding(bottom = 24.dp)
        )

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = CardDefaults.elevatedShape
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            val ok = withContext(Dispatchers.IO) {
                                EventService.connectDevice(context, microcontrollerId = 1)
                            }
                            if (ok) {
                                // Re-register FCM token so push notifications target this alarm system
                                FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                                    if (task.isSuccessful) {
                                        task.result?.let { AlarmFirebaseMessagingService.registerTokenWithBackend(context, it) }
                                    }
                                }
                            }
                            Toast.makeText(
                                context,
                                if (ok) "ESP32 linked. Real sensor events and notifications will now appear." else "Could not link device. Check backend and try again.",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Link ESP32 (show real sensor events)")
                }
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = onSignOut,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary)
                ) {
                    Text("Sign out", fontWeight = FontWeight.SemiBold)
                }
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = { /* Delete account – UI only */ },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Delete account", color = MaterialTheme.colorScheme.error)
                }
                Spacer(Modifier.height(24.dp))
                Text(
                    text = "Authorised users",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                Text(
                    text = "Add or view users and their permissions for your home security system. (Coming soon)",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.9f)
                )
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = { /* Authorised users – UI only */ },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Manage authorised users")
                }
            }
        }
    }
}
