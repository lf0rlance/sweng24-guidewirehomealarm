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
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
    var pairPassword by remember { mutableStateOf("") }

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
                Text(
                    text = "1. Pair to your home (once)",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                Text(
                    text = "Enter the alarm system password for an unpaired home (from your admin/setup). Then link each ESP32 below.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.typography.bodySmall.color.copy(alpha = 0.85f),
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                OutlinedTextField(
                    value = pairPassword,
                    onValueChange = { pairPassword = it },
                    label = { Text("Home alarm password (8+ characters)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            val pwd = pairPassword.trim()
                            if (pwd.length < 8) {
                                Toast.makeText(
                                    context,
                                    "Password must be at least 8 characters.",
                                    Toast.LENGTH_SHORT
                                ).show()
                                return@launch
                            }
                            val ok = withContext(Dispatchers.IO) {
                                EventService.pairWithHome(context, pwd)
                            }
                            Toast.makeText(
                                context,
                                if (ok) "Paired to your home. You can link ESP32s below." else "Pairing failed. Check password, or ask an admin to assign your account.",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Pair account to home")
                }
                Spacer(Modifier.height(16.dp))
                Text(
                    text = "2. Link ESP32 hardware",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
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
                                if (ok) "ESP32 #1 linked (esp32_001). Real sensor events and notifications will now appear." else "Could not link device. Check backend and try again.",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Link 1st ESP32 (esp32_001)")
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        scope.launch {
                            val ok = withContext(Dispatchers.IO) {
                                EventService.connectDevice(context, microcontrollerId = 2)
                            }
                            if (ok) {
                                FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                                    if (task.isSuccessful) {
                                        task.result?.let { AlarmFirebaseMessagingService.registerTokenWithBackend(context, it) }
                                    }
                                }
                            }
                            Toast.makeText(
                                context,
                                if (ok) "ESP32 #2 linked (esp32_002)." else "Could not link device. Check backend and try again.",
                                Toast.LENGTH_LONG
                            ).show()
                        }
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Link 2nd ESP32 (esp32_002)")
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
