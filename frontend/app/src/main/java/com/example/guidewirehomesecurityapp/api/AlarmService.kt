package com.example.guidewirehomesecurityapp.api

import android.content.Context
import com.example.guidewirehomesecurityapp.BuildConfig
import com.example.guidewirehomesecurityapp.auth.BackendAuthService
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Get and set armed state for the logged-in user's alarm system.
 * Backend: GET /api/alarm, PUT /api/alarm with JWT.
 */
object AlarmService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()

    private fun serverBaseUrl(): String =
        BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")

    /**
     * GET /api/alarm — current armed state. Call from background thread (e.g. Dispatchers.IO).
     * @return true = armed, false = disarmed, null = error or not linked
     */
    fun getArmedStatus(context: Context): Boolean? {
        val url = "${serverBaseUrl()}/api/alarm"
        val token = BackendAuthService.getToken(context) ?: return null
        val request = Request.Builder()
            .url(url)
            .get()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return try {
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return null
                val body = response.body?.string() ?: return null
                val obj = JSONObject(body)
                obj.optBoolean("armed", false)
            }
        } catch (_: Exception) {
            null
        }
    }

    /**
     * PUT /api/alarm — set armed state. Call from background thread.
     * @return true = success, false = failure
     */
    fun setArmedStatus(context: Context, armed: Boolean, disarmCode: String? = null): Boolean {
        val url = "${serverBaseUrl()}/api/alarm"
        val token = BackendAuthService.getToken(context) ?: return false
        val body = JSONObject().apply {
            put("armed", armed)
            if (!armed && !disarmCode.isNullOrBlank()) {
                put("disarm_code", disarmCode.trim())
            }
        }
            .toString()
            .toRequestBody("application/json".toMediaType())
        val request = Request.Builder()
            .url(url)
            .put(body)
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
