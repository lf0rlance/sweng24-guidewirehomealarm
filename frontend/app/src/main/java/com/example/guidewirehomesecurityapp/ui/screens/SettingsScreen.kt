package com.example.guidewirehomesecurityapp.ui.screens

import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.window.Dialog
import com.example.guidewirehomesecurityapp.api.HomeService
import com.example.guidewirehomesecurityapp.auth.BackendAuthService
import com.example.guidewirehomesecurityapp.ui.components.HomeRoleChipSelector
import com.example.guidewirehomesecurityapp.ui.components.ScreenTitleWithLogo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun SettingsScreen(
    modifier: Modifier = Modifier,
    onSignOut: () -> Unit = {}
) {
    val scrollState = rememberScrollState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val homeRole = BackendAuthService.getHomeRole(context) ?: ""
    var members by remember { mutableStateOf<List<HomeService.HomeMember>>(emptyList()) }
    var pending by remember { mutableStateOf<List<HomeService.PendingDisarm>>(emptyList()) }
    var editingMember by remember { mutableStateOf<HomeService.HomeMember?>(null) }
    var rolePick by remember { mutableStateOf("spouse") }
    var removeMember by remember { mutableStateOf<HomeService.HomeMember?>(null) }

    fun refreshOwnerData() {
        scope.launch {
            members = withContext(Dispatchers.IO) { HomeService.listMembers(context) }
            pending = withContext(Dispatchers.IO) { HomeService.listPendingDisarmRequests(context) }
        }
    }

    LaunchedEffect(homeRole) {
        if (homeRole == "owner") refreshOwnerData()
    }

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

        Text(
            text = "Home pairing and ESP32 devices are set up by your administrator.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        if (homeRole == "owner") {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = CardDefaults.elevatedShape
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "Pending disarm approvals",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.height(8.dp))
                    if (pending.isEmpty()) {
                        Text(
                            "No pending requests.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    } else {
                        pending.forEach { p ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 6.dp),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    "User #${p.requestedByUserId}",
                                    style = MaterialTheme.typography.bodyMedium,
                                    modifier = Modifier.weight(1f)
                                )
                                TextButton(onClick = {
                                    scope.launch {
                                        val ok = withContext(Dispatchers.IO) {
                                            HomeService.approveDisarm(context, p.id)
                                        }
                                        Toast.makeText(
                                            context,
                                            if (ok) "Disarm approved" else "Failed",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                        refreshOwnerData()
                                    }
                                }) { Text("Approve") }
                                TextButton(onClick = {
                                    scope.launch {
                                        val ok = withContext(Dispatchers.IO) {
                                            HomeService.denyDisarm(context, p.id)
                                        }
                                        Toast.makeText(
                                            context,
                                            if (ok) "Request denied" else "Failed",
                                            Toast.LENGTH_SHORT
                                        ).show()
                                        refreshOwnerData()
                                    }
                                }) { Text("Deny") }
                            }
                        }
                    }
                    OutlinedButton(onClick = { refreshOwnerData() }, modifier = Modifier.fillMaxWidth()) {
                        Text("Refresh pending")
                    }
                }
            }

            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                shape = CardDefaults.elevatedShape
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "Household members",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Change roles or remove users added by your administrator. Spouse/partner cannot manage this list.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    members.forEach { m ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
                            ),
                            shape = RoundedCornerShape(14.dp),
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 14.dp, vertical = 12.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        m.username,
                                        style = MaterialTheme.typography.titleSmall,
                                        fontWeight = FontWeight.Medium
                                    )
                                    Text(
                                        m.email,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        maxLines = 2
                                    )
                                    Text(
                                        "Role: ${m.homeRole}",
                                        style = MaterialTheme.typography.labelMedium,
                                        color = MaterialTheme.colorScheme.primary
                                    )
                                }
                                TextButton(onClick = {
                                    editingMember = m
                                    rolePick = m.homeRole
                                }) { Text("Edit") }
                            }
                        }
                    }
                    OutlinedButton(onClick = { refreshOwnerData() }, modifier = Modifier.fillMaxWidth()) {
                        Text("Refresh list")
                    }
                }
            }
        } else if (homeRole == "spouse") {
            Text(
                "Only the homeowner can add or remove users in Settings.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(bottom = 16.dp)
            )
        }

        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
            shape = CardDefaults.elevatedShape
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
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
            }
        }
    }

    editingMember?.let { m ->
        Dialog(onDismissRequest = { editingMember = null }) {
            Surface(
                shape = RoundedCornerShape(28.dp),
                color = MaterialTheme.colorScheme.surface,
                tonalElevation = 2.dp,
                shadowElevation = 6.dp,
            ) {
                Column(
                    Modifier
                        .widthIn(min = 300.dp, max = 420.dp)
                        .padding(24.dp)
                        .verticalScroll(rememberScrollState())
                ) {
                    Text(
                        "Member role",
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        m.username,
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 4.dp)
                    )
                    Text(
                        m.email,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(bottom = 16.dp)
                    )
                    Text("Home role", style = MaterialTheme.typography.labelLarge)
                    Spacer(Modifier.height(8.dp))
                    HomeRoleChipSelector(
                        selectedRole = rolePick,
                        onRoleSelected = { rolePick = it }
                    )
                    Spacer(Modifier.height(16.dp))
                    TextButton(
                        onClick = {
                            removeMember = m
                            editingMember = null
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Remove from home", color = MaterialTheme.colorScheme.error)
                    }
                    Spacer(Modifier.height(8.dp))
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.End
                    ) {
                        TextButton(onClick = { editingMember = null }) { Text("Cancel") }
                        TextButton(onClick = {
                            scope.launch {
                                val ok = withContext(Dispatchers.IO) {
                                    HomeService.updateMemberHomeRole(context, m.id, rolePick)
                                }
                                Toast.makeText(
                                    context,
                                    if (ok) "Role updated" else "Could not update",
                                    Toast.LENGTH_SHORT
                                ).show()
                                editingMember = null
                                refreshOwnerData()
                            }
                        }) { Text("Save") }
                    }
                }
            }
        }
    }

    removeMember?.let { m ->
        AlertDialog(
            onDismissRequest = { removeMember = null },
            title = { Text("Remove ${m.username}?") },
            text = { Text("They will be unlinked from this home; their account stays.") },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        val ok = withContext(Dispatchers.IO) { HomeService.removeMember(context, m.id) }
                        Toast.makeText(
                            context,
                            if (ok) "Removed" else "Failed",
                            Toast.LENGTH_SHORT
                        ).show()
                        removeMember = null
                        refreshOwnerData()
                    }
                }) { Text("Remove", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = { TextButton(onClick = { removeMember = null }) { Text("Cancel") } }
        )
    }
}
