package com.example.guidewirehomesecurityapp.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.SensorDoor
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.example.guidewirehomesecurityapp.api.AdminHome
import com.example.guidewirehomesecurityapp.api.AdminService
import com.example.guidewirehomesecurityapp.auth.BackendAuthService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AdminDashboardScreen(
    modifier: Modifier = Modifier,
    onSignOut: () -> Unit = {}
) {
    val context = LocalContext.current
    var homes by remember { mutableStateOf<List<AdminHome>>(emptyList()) }
    var offlineCount by remember { mutableStateOf(0) }
    var loading by remember { mutableStateOf(true) }
    var addHomeResult by remember { mutableStateOf<AdminService.AddHomeResult?>(null) }
    var expandedHomeId by remember { mutableStateOf<Int?>(null) }
    var sensorDialogHome by remember { mutableStateOf<AdminHome?>(null) }
    var userDialogHome by remember { mutableStateOf<AdminHome?>(null) }
    var notifyDialogHome by remember { mutableStateOf<AdminHome?>(null) }
    var nameEditHome by remember { mutableStateOf<AdminHome?>(null) }
    var deleteConfirmHome by remember { mutableStateOf<AdminHome?>(null) }
    val scope = rememberCoroutineScope()

    fun loadData() {
        loading = true
        scope.launch {
            val (h, o) = withContext(Dispatchers.IO) {
                AdminService.listHomes(context) to AdminService.listOffline(context).size
            }
            homes = h
            offlineCount = o
            loading = false
        }
    }

    LaunchedEffect(Unit) { loadData() }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("Admin", fontWeight = FontWeight.Bold)
                        BackendAuthService.getUsername(context)?.let { un ->
                            Text(
                                " · $un",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.8f)
                            )
                        }
                    }
                },
                actions = {
                    TextButton(onClick = onSignOut) {
                        Text("Sign out")
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = {
                    scope.launch {
                        val result = withContext(Dispatchers.IO) { AdminService.addHome(context) }
                        addHomeResult = result
                        if (result != null) {
                            loadData()
                            Toast.makeText(context, "Home added: ${result.deviceId}", Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(context, "Failed to add home", Toast.LENGTH_SHORT).show()
                        }
                    }
                },
                shape = RoundedCornerShape(16.dp),
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary
            ) {
                Icon(Icons.Default.Add, contentDescription = "Add home")
            }
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(
                    brush = Brush.linearGradient(
                        colors = listOf(
                            MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f),
                            MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
                        ),
                        start = Offset(0f, 0f),
                        end = Offset(500f, 800f)
                    )
                )
        ) {
            if (loading && homes.isEmpty()) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    if (offlineCount > 0) {
                        item {
                            Card(
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Text(
                                    modifier = Modifier.padding(12.dp),
                                    text = "$offlineCount device(s) offline — consider notifying homeowners",
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                        }
                    }
                    items(homes) { home ->
                        AdminHomeCard(
                            home = home,
                            expanded = expandedHomeId == home.alarmSystemId,
                            onExpand = { expandedHomeId = if (expandedHomeId == home.alarmSystemId) null else home.alarmSystemId },
                            onEditSensors = { sensorDialogHome = home },
                            onManageUsers = { userDialogHome = home },
                            onNotify = { notifyDialogHome = home },
                            onEditName = { nameEditHome = home },
                            onDelete = { deleteConfirmHome = home }
                        )
                    }
                }
            }
        }
    }

    addHomeResult?.let { result ->
        AlertDialog(
            onDismissRequest = { addHomeResult = null },
            title = { Text("New home added") },
            text = {
                Column {
                    Text("Device ID for customer / ESP32: ${result.deviceId}")
                    Text("Alarm system ID: ${result.alarmSystemId}", style = MaterialTheme.typography.bodySmall)
                }
            },
            confirmButton = { TextButton(onClick = { addHomeResult = null }) { Text("OK") } }
        )
    }

    sensorDialogHome?.let { home ->
        SensorLabelsDialog(
            home = home,
            onDismiss = { sensorDialogHome = null },
            onSave = { labels ->
                scope.launch {
                    val ok = withContext(Dispatchers.IO) {
                        AdminService.setSensorLabels(context, home.alarmSystemId, labels)
                    }
                    if (ok) {
                        loadData()
                        sensorDialogHome = null
                        Toast.makeText(context, "Sensor names saved", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        )
    }

    userDialogHome?.let { home ->
        UsersDialog(
            home = home,
            onDismiss = { userDialogHome = null },
            onUserAdded = { loadData() }
        )
    }

    notifyDialogHome?.let { home ->
        NotifyDialog(
            home = home,
            onDismiss = { notifyDialogHome = null },
            onSend = { title, body ->
                scope.launch {
                    val n = withContext(Dispatchers.IO) {
                        AdminService.notifyHomeowner(context, home.alarmSystemId, title, body)
                    }
                    notifyDialogHome = null
                    Toast.makeText(context, "Sent to $n device(s)", Toast.LENGTH_SHORT).show()
                }
            }
        )
    }

    nameEditHome?.let { home ->
        var editName by remember(home.alarmSystemId) { mutableStateOf(home.name.ifBlank { home.deviceId }) }
        AlertDialog(
            onDismissRequest = { nameEditHome = null },
            title = { Text("Edit name") },
            text = {
                OutlinedTextField(
                    value = editName,
                    onValueChange = { editName = it },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("Display name") }
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        val ok = withContext(Dispatchers.IO) {
                            AdminService.updateHomeName(context, home.alarmSystemId, editName)
                        }
                        if (ok) { loadData(); nameEditHome = null; Toast.makeText(context, "Saved", Toast.LENGTH_SHORT).show() }
                    }
                }) { Text("Save") }
            },
            dismissButton = { TextButton(onClick = { nameEditHome = null }) { Text("Cancel") } }
        )
    }

    deleteConfirmHome?.let { home ->
        AlertDialog(
            onDismissRequest = { deleteConfirmHome = null },
            title = { Text("Delete alarm system?") },
            text = {
                Text("${home.name.ifBlank { home.deviceId }} will be removed. Users will be unlinked (not deleted).")
            },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        val (ok, errMsg) = withContext(Dispatchers.IO) {
                            AdminService.deleteHome(context, home.alarmSystemId)
                        }
                        deleteConfirmHome = null
                        if (ok) {
                            loadData()
                            Toast.makeText(context, "Deleted", Toast.LENGTH_SHORT).show()
                        } else {
                            Toast.makeText(context, "Delete failed: ${errMsg ?: "Unknown"}", Toast.LENGTH_LONG).show()
                        }
                    }
                }) { Text("Delete", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = { TextButton(onClick = { deleteConfirmHome = null }) { Text("Cancel") } }
        )
    }
}

@Composable
private fun AdminHomeCard(
    home: AdminHome,
    expanded: Boolean,
    onExpand: () -> Unit,
    onEditSensors: () -> Unit,
    onManageUsers: () -> Unit,
    onNotify: () -> Unit,
    onEditName: () -> Unit,
    onDelete: () -> Unit
) {
    val displayName = home.name.ifBlank { home.deviceId.ifBlank { "System #${home.alarmSystemId}" } }
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        onClick = onExpand
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = displayName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "${home.deviceId} · Users: ${home.userCount} · Sensors: ${home.sensorLabels.size}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (home.offline) {
                        OutlinedButton(
                            onClick = onNotify,
                            modifier = Modifier.padding(end = 8.dp)
                        ) {
                            Icon(Icons.Default.Notifications, contentDescription = null, Modifier.padding(end = 4.dp))
                            Text("Notify")
                        }
                        Text(
                            text = "OFFLINE",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
            }
            if (expanded) {
                Spacer(Modifier.height(12.dp))
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedButton(
                            onClick = onEditName,
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Default.Edit, null, Modifier.padding(end = 4.dp))
                            Text("Name", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        OutlinedButton(
                            onClick = onEditSensors,
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Default.SensorDoor, null, Modifier.padding(end = 4.dp))
                            Text("Sensors", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        OutlinedButton(
                            onClick = onManageUsers,
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Default.Person, null, Modifier.padding(end = 4.dp))
                            Text("Users", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedButton(
                            onClick = onNotify,
                            modifier = Modifier.weight(1f)
                        ) {
                            Icon(Icons.Default.Notifications, null, Modifier.padding(end = 4.dp))
                            Text("Notify", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        OutlinedButton(
                            onClick = onDelete,
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
                        ) {
                            Icon(Icons.Default.Delete, null, Modifier.padding(end = 4.dp))
                            Text("Delete", style = MaterialTheme.typography.labelSmall, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SensorLabelsDialog(
    home: AdminHome,
    onDismiss: () -> Unit,
    onSave: (List<String>) -> Unit
) {
    var text by remember(home.alarmSystemId) {
        mutableStateOf(home.sensorLabels.joinToString("\n"))
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Sensor names — ${home.name.ifBlank { home.deviceId }}") },
        text = {
            Column {
                Text("One name per line (e.g. Front door, Back window)", style = MaterialTheme.typography.bodySmall)
                Spacer(Modifier.height(8.dp))
                BasicTextField(
                    value = text,
                    onValueChange = { text = it },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp)
                        .background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f), RoundedCornerShape(8.dp))
                        .padding(8.dp),
                    textStyle = MaterialTheme.typography.bodyMedium
                )
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(text.split("\n").map { it.trim() }.filter { it.isNotBlank() })
            }) { Text("Save") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}

@Composable
private fun UsersDialog(
    home: AdminHome,
    onDismiss: () -> Unit,
    onUserAdded: () -> Unit
) {
    var users by remember(home.alarmSystemId) { mutableStateOf<List<AdminService.HomeUser>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var showAddForm by remember { mutableStateOf(false) }
    var showLinkForm by remember { mutableStateOf(false) }
    var editUser by remember { mutableStateOf<AdminService.HomeUser?>(null) }
    var removeConfirmUser by remember { mutableStateOf<AdminService.HomeUser?>(null) }
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    LaunchedEffect(home.alarmSystemId) {
        users = withContext(Dispatchers.IO) { AdminService.listUsers(context, home.alarmSystemId) }
        loading = false
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Users — ${home.name.ifBlank { home.deviceId }}") },
        text = {
            Column {
                if (loading) CircularProgressIndicator()
                else {
                    users.forEach { u ->
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("${u.username} (${u.email}) · ${u.accessLevel}", style = MaterialTheme.typography.bodyMedium)
                            Row {
                                IconButton(onClick = { editUser = u }) {
                                    Icon(Icons.Default.Edit, contentDescription = "Edit")
                                }
                                IconButton(onClick = { removeConfirmUser = u }) {
                                    Icon(Icons.Default.Delete, contentDescription = "Remove")
                                }
                            }
                        }
                    }
                    if (showAddForm) {
                        AddUserForm(
                            onAdd = { username, email, password, phone, accessLevel ->
                                scope.launch {
                                    val ok = withContext(Dispatchers.IO) {
                                        AdminService.addUser(context, home.alarmSystemId, username, email, password, phone, accessLevel)
                                    }
                                    if (ok) {
                                        onUserAdded()
                                        showAddForm = false
                                        users = withContext(Dispatchers.IO) { AdminService.listUsers(context, home.alarmSystemId) }
                                        Toast.makeText(context, "User created", Toast.LENGTH_SHORT).show()
                                    } else {
                                        Toast.makeText(context, "Failed (e.g. email already exists)", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            },
                            onCancel = { showAddForm = false }
                        )
                    } else if (showLinkForm) {
                        LinkExistingUserForm(
                            onLink = { email, accessLevel ->
                                scope.launch {
                                    val ok = withContext(Dispatchers.IO) {
                                        AdminService.linkExistingUser(context, home.alarmSystemId, email, accessLevel)
                                    }
                                    if (ok) {
                                        onUserAdded()
                                        showLinkForm = false
                                        users = withContext(Dispatchers.IO) { AdminService.listUsers(context, home.alarmSystemId) }
                                        Toast.makeText(context, "User linked", Toast.LENGTH_SHORT).show()
                                    } else {
                                        Toast.makeText(context, "Failed (user not found or linked elsewhere)", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            },
                            onCancel = { showLinkForm = false }
                        )
                    } else {
                        Row {
                            TextButton(onClick = { showAddForm = true }) { Text("Create new") }
                            TextButton(onClick = { showLinkForm = true }) { Text("Add existing") }
                        }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Close") } }
    )

    editUser?.let { u ->
        var username by remember(u.id) { mutableStateOf(u.username) }
        var email by remember(u.id) { mutableStateOf(u.email) }
        var phone by remember(u.id) { mutableStateOf(u.phone) }
        var password by remember(u.id) { mutableStateOf("") }
        var accessLevel by remember(u.id) { mutableStateOf(u.accessLevel.ifBlank { "owner" }) }
        AlertDialog(
            onDismissRequest = { editUser = null },
            title = { Text("Edit user") },
            text = {
                Column {
                    OutlinedTextField(value = username, onValueChange = { username = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("Username") })
                    Spacer(Modifier.height(4.dp))
                    OutlinedTextField(value = email, onValueChange = { email = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("Email") })
                    Spacer(Modifier.height(4.dp))
                    OutlinedTextField(value = phone, onValueChange = { phone = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("Phone") })
                    Spacer(Modifier.height(4.dp))
                    OutlinedTextField(value = password, onValueChange = { password = it }, modifier = Modifier.fillMaxWidth(), singleLine = true, label = { Text("New password (optional)") })
                    Spacer(Modifier.height(8.dp))
                    AccessLevelPicker(value = accessLevel, onValueChange = { accessLevel = it })
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        val ok = withContext(Dispatchers.IO) {
                            AdminService.updateUser(
                                context,
                                home.alarmSystemId,
                                u.id,
                                username,
                                email,
                                phone,
                                password.takeIf { it.isNotBlank() },
                                accessLevel
                            )
                        }
                        editUser = null
                        if (ok) {
                            users = withContext(Dispatchers.IO) { AdminService.listUsers(context, home.alarmSystemId) }
                            onUserAdded()
                            Toast.makeText(context, "Saved", Toast.LENGTH_SHORT).show()
                        }
                    }
                }) { Text("Save") }
            },
            dismissButton = { TextButton(onClick = { editUser = null }) { Text("Cancel") } }
        )
    }

    removeConfirmUser?.let { u ->
        AlertDialog(
            onDismissRequest = { removeConfirmUser = null },
            title = { Text("Remove user from home?") },
            text = { Text("${u.username} will be unlinked from this home (account kept).") },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        val ok = withContext(Dispatchers.IO) { AdminService.removeUser(context, home.alarmSystemId, u.id) }
                        removeConfirmUser = null
                        if (ok) {
                            users = withContext(Dispatchers.IO) { AdminService.listUsers(context, home.alarmSystemId) }
                            onUserAdded()
                            Toast.makeText(context, "Removed", Toast.LENGTH_SHORT).show()
                        }
                    }
                }) { Text("Remove", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = { TextButton(onClick = { removeConfirmUser = null }) { Text("Cancel") } }
        )
    }
}

@Composable
private fun AddUserForm(
    onAdd: (username: String, email: String, password: String, phone: String?, accessLevel: String) -> Unit,
    onCancel: () -> Unit
) {
    var username by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var accessLevel by remember { mutableStateOf("owner") }
    Column {
        OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("Username") }
        )
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("Email") }
        )
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("Password") }
        )
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = phone,
            onValueChange = { phone = it },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("Phone (optional)") }
        )
        Spacer(Modifier.height(8.dp))
        AccessLevelPicker(value = accessLevel, onValueChange = { accessLevel = it })
        Row {
            TextButton(onClick = { onAdd(username, email, password, phone.takeIf { it.isNotBlank() }, accessLevel) }) { Text("Create") }
            TextButton(onClick = onCancel) { Text("Cancel") }
        }
    }
}

@Composable
private fun LinkExistingUserForm(
    onLink: (email: String, accessLevel: String) -> Unit,
    onCancel: () -> Unit
) {
    var email by remember { mutableStateOf("") }
    var accessLevel by remember { mutableStateOf("owner") }
    Column {
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            label = { Text("Existing user's email") }
        )
        Spacer(Modifier.height(8.dp))
        AccessLevelPicker(value = accessLevel, onValueChange = { accessLevel = it })
        Row {
            TextButton(onClick = { onLink(email, accessLevel) }) { Text("Link") }
            TextButton(onClick = onCancel) { Text("Cancel") }
        }
    }
}

@Composable
private fun AccessLevelPicker(
    value: String,
    onValueChange: (String) -> Unit
) {
    val options = listOf("owner", "trusted_full", "child", "arm_only", "viewer")
    var expanded by remember { mutableStateOf(false) }
    Column {
        Text("Access level", style = MaterialTheme.typography.bodySmall)
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = value,
            onValueChange = { },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            readOnly = true,
            label = { Text("Role") },
            trailingIcon = {
                TextButton(onClick = { expanded = true }) { Text("Change") }
            }
        )
        DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
            options.forEach { opt ->
                DropdownMenuItem(
                    text = { Text(opt) },
                    onClick = {
                        onValueChange(opt)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
private fun NotifyDialog(
    home: AdminHome,
    onDismiss: () -> Unit,
    onSend: (title: String, body: String) -> Unit
) {
    val defaultTitle = if (home.offline) "Sensor offline" else "Update"
    val defaultBody = if (home.offline) "One or more sensors have been offline. Please check your system." else ""
    var title by remember(home.alarmSystemId) { mutableStateOf(defaultTitle) }
    var body by remember(home.alarmSystemId) { mutableStateOf(defaultBody) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Notify homeowner — ${home.name.ifBlank { home.deviceId }}") },
        text = {
            Column {
                Text("Title")
                BasicTextField(
                    value = title,
                    onValueChange = { title = it },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    textStyle = MaterialTheme.typography.bodyMedium
                )
                Spacer(Modifier.height(8.dp))
                Text("Message")
                BasicTextField(
                    value = body,
                    onValueChange = { body = it },
                    modifier = Modifier.fillMaxWidth(),
                    textStyle = MaterialTheme.typography.bodyMedium
                )
            }
        },
        confirmButton = { TextButton(onClick = { onSend(title, body) }) { Text("Send") } },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancel") } }
    )
}
