package com.example.guidewirehomesecurityapp.api

import com.example.guidewirehomesecurityapp.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import java.util.concurrent.TimeUnit

/**
 * Fetches processed sensor events from the backend.
 * Backend receives events from ESP32 (POST /api/events) and exposes them at GET /events.
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
     * GET /events — returns all events the backend has received (validated).
     * Call from a background thread (e.g. Dispatchers.IO).
     */
    fun getEvents(serverBaseUrl: String = serverBaseUrl()): List<SensorEvent> {
        val url = "$serverBaseUrl/events"
        val request = Request.Builder().url(url).get().build()
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
}
