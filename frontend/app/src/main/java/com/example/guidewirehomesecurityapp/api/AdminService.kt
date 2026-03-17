package com.example.guidewirehomesecurityapp.api

import android.content.Context
import com.example.guidewirehomesecurityapp.BuildConfig
import com.example.guidewirehomesecurityapp.auth.BackendAuthService
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Admin-only API (requires role=admin JWT). No home address is ever sent or received. */
object AdminService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    private fun baseUrl(context: Context): String =
        BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")

    private fun authRequest(context: Context, path: String, method: String = "GET", body: String? = null): Request {
        val token = BackendAuthService.getToken(context) ?: ""
        val url = "${baseUrl(context)}/api/admin$path"
        val builder = Request.Builder().url(url).addHeader("Authorization", "Bearer $token")
        when (method) {
            "GET" -> builder.get()
            "POST" -> builder.post((body ?: "{}").toRequestBody("application/json".toMediaType()))
            "PUT" -> builder.put((body ?: "{}").toRequestBody("application/json".toMediaType()))
            "PATCH" -> builder.patch((body ?: "{}").toRequestBody("application/json".toMediaType()))
            "DELETE" -> builder.delete()
            else -> builder.get()
        }
        if (body != null && method != "GET")
            builder.addHeader("Content-Type", "application/json")
        return builder.build()
    }

    fun listHomes(context: Context): List<AdminHome> = run {
        val req = authRequest(context, "/homes")
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val arr = JSONArray(response.body?.string() ?: "[]")
                List(arr.length()) { i ->
                    val o = arr.getJSONObject(i)
                    AdminHome(
                        alarmSystemId = o.optInt("alarm_system_id", 0),
                        name = o.optString("name", ""),
                        microcontrollerId = o.optInt("microcontroller_id", 0),
                        deviceId = o.optString("device_id", ""),
                        currentState = o.optString("current_state", ""),
                        lastSeen = if (o.has("last_seen") && !o.isNull("last_seen")) o.optDouble("last_seen", 0.0) else null,
                        offline = o.optBoolean("offline", false),
                        sensorLabels = jsonArrayToStringList(o.optJSONArray("sensor_labels")),
                        userCount = o.optInt("user_count", 0)
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    private fun jsonArrayToStringList(arr: JSONArray?): List<String> {
        if (arr == null) return emptyList()
        return List(arr.length()) { i -> arr.optString(i, "") }
    }

    fun updateHomeName(context: Context, alarmSystemId: Int, name: String): Boolean = run {
        val body = JSONObject().apply { put("name", name) }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId", "PATCH", body)
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    /** @return Pair(success, errorMessage?) */
    fun deleteHome(context: Context, alarmSystemId: Int): Pair<Boolean, String?> = run {
        val req = authRequest(context, "/homes/$alarmSystemId", "DELETE")
        try {
            client.newCall(req).execute().use { response ->
                if (response.isSuccessful) return Pair(true, null)
                val body = response.body?.string() ?: ""
                val msg = try {
                    org.json.JSONObject(body).optString("detail", "HTTP ${response.code}")
                } catch (_: Exception) {
                    "HTTP ${response.code}"
                }
                return Pair(false, msg)
            }
        } catch (e: Exception) {
            Pair(false, e.message ?: "Network error")
        }
    }

    data class AddHomeResult(val alarmSystemId: Int, val deviceId: String)
    fun addHome(context: Context): AddHomeResult? = run {
        val req = authRequest(context, "/homes", "POST")
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return null
                val o = JSONObject(response.body?.string() ?: "{}")
                AddHomeResult(
                    alarmSystemId = o.optInt("alarm_system_id", 0),
                    deviceId = o.optString("device_id", "")
                )
            }
        } catch (_: Exception) {
            null
        }
    }

    fun getSensorLabels(context: Context, alarmSystemId: Int): List<String> = run {
        val req = authRequest(context, "/homes/$alarmSystemId/sensors")
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val o = JSONObject(response.body?.string() ?: "{}")
                jsonArrayToStringList(o.optJSONArray("labels"))
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun setSensorLabels(context: Context, alarmSystemId: Int, labels: List<String>): Boolean = run {
        val body = JSONObject().apply { put("labels", JSONArray(labels)) }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId/sensors", "PUT", body)
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    data class HomeUser(
        val id: Int,
        val username: String,
        val email: String,
        val phone: String,
        val role: String,
        val accessLevel: String
    )
    fun listUsers(context: Context, alarmSystemId: Int): List<HomeUser> = run {
        val req = authRequest(context, "/homes/$alarmSystemId/users")
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val arr = JSONArray(response.body?.string() ?: "[]")
                List(arr.length()) { i ->
                    val o = arr.getJSONObject(i)
                    HomeUser(
                        id = o.optInt("id", 0),
                        username = o.optString("username", ""),
                        email = o.optString("email", ""),
                        phone = o.optString("phone", ""),
                        role = o.optString("role", "user"),
                        accessLevel = o.optString("access_level", "owner")
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun addUser(
        context: Context,
        alarmSystemId: Int,
        username: String,
        email: String,
        password: String,
        phone: String?,
        accessLevel: String
    ): Boolean = run {
        val body = JSONObject().apply {
            put("username", username)
            put("email", email)
            put("password", password)
            put("phone", phone ?: "")
            put("access_level", accessLevel)
        }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId/users", "POST", body)
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    fun updateUser(
        context: Context,
        alarmSystemId: Int,
        userId: Int,
        username: String?,
        email: String?,
        phone: String?,
        password: String?,
        accessLevel: String?
    ): Boolean = run {
        val body = JSONObject().apply {
            if (username != null) put("username", username)
            if (email != null) put("email", email)
            if (phone != null) put("phone", phone)
            if (password != null) put("password", password)
            if (accessLevel != null) put("access_level", accessLevel)
        }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId/users/$userId", "PUT", body)
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    fun linkExistingUser(
        context: Context,
        alarmSystemId: Int,
        email: String,
        accessLevel: String
    ): Boolean = run {
        val body = JSONObject().apply {
            put("email", email)
            put("access_level", accessLevel)
        }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId/users/link", "POST", body)
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    fun removeUser(context: Context, alarmSystemId: Int, userId: Int): Boolean = run {
        val req = authRequest(context, "/homes/$alarmSystemId/users/$userId", "DELETE")
        try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    data class OfflineDevice(val microcontrollerId: Int, val alarmSystemId: Int, val lastSeen: Double)
    fun listOffline(context: Context): List<OfflineDevice> = run {
        val req = authRequest(context, "/offline")
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val arr = JSONArray(response.body?.string() ?: "[]")
                List(arr.length()) { i ->
                    val o = arr.getJSONObject(i)
                    OfflineDevice(
                        microcontrollerId = o.optInt("microcontroller_id", 0),
                        alarmSystemId = o.optInt("alarm_system_id", 0),
                        lastSeen = o.optDouble("last_seen", 0.0)
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun notifyHomeowner(context: Context, alarmSystemId: Int, title: String, body: String): Int = run {
        val reqBody = JSONObject().apply {
            put("title", title)
            put("body", body)
        }.toString()
        val req = authRequest(context, "/homes/$alarmSystemId/notify", "POST", reqBody)
        try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return 0
                val o = JSONObject(response.body?.string() ?: "{}")
                o.optInt("sent_to_devices", 0)
            }
        } catch (_: Exception) {
            0
        }
    }
}

data class AdminHome(
    val alarmSystemId: Int,
    val name: String,
    val microcontrollerId: Int,
    val deviceId: String,
    val currentState: String,
    val lastSeen: Double?,
    val offline: Boolean,
    val sensorLabels: List<String>,
    val userCount: Int
)
