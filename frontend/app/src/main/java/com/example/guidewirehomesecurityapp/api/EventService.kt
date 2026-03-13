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

/**
 * Fetches sensor events for the logged-in user's alarm system from the backend.
 * GET /events requires Authorization Bearer token; returns only events for that user's system.
 */
object EventService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    /** Server base URL without /api (e.g. http://10.0.2.2:5000) */
    fun serverBaseUrl(): String =
        BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")

    /**
     * GET /events — returns events for the authenticated user's alarm system only.
     * Requires JWT (from login). Call from a background thread (e.g. Dispatchers.IO).
     */
    fun getEvents(context: Context, serverBaseUrl: String = serverBaseUrl()): List<SensorEvent> {
        val url = "$serverBaseUrl/events"
        val token = BackendAuthService.getToken(context)
        val requestBuilder = Request.Builder().url(url).get()
        if (!token.isNullOrBlank()) {
            requestBuilder.addHeader("Authorization", "Bearer $token")
        }
        val request = requestBuilder.build()
        return try {
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val body = response.body?.string() ?: return emptyList()
                val arr = JSONArray(body)
                List(arr.length()) { i ->
                    val obj = arr.getJSONObject(i)
                    SensorEvent(
                        device_id = obj.optString("device_id", ""),
                        event_type = obj.optString("event_type", ""),
                        count = obj.optInt("count", 0),
                        timestamp = obj.optDouble("timestamp", 0.0)
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    /**
     * POST /api/device/connect — link ESP32 (esp32_001 = microcontroller_id 1) to your account
     * so real hardware sensor events show in the app. Call from background thread (e.g. Dispatchers.IO).
     * @return true if linked successfully, false otherwise.
     */
    fun connectDevice(context: Context, microcontrollerId: Int = 1, serverBaseUrl: String = serverBaseUrl()): Boolean {
        val url = "$serverBaseUrl/api/device/connect"
        val token = BackendAuthService.getToken(context)
        if (token.isNullOrBlank()) return false
        val body = JSONObject().apply { put("microcontroller_id", microcontrollerId) }
            .toString()
            .toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(url)
            .post(body)
            .addHeader("Authorization", "Bearer $token")
            .addHeader("Content-Type", "application/json")
            .build()
        return try {
            client.newCall(request).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }
}
