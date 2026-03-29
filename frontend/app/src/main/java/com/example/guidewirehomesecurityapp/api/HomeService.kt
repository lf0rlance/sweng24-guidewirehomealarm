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

/** Homeowner APIs: /api/home/members and alarm disarm approval. */
object HomeService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    private fun base(context: Context) =
        BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")

    private fun auth(context: Context, path: String, method: String, body: String? = null): Request {
        val token = BackendAuthService.getToken(context) ?: ""
        val b = Request.Builder()
            .url("${base(context)}$path")
            .addHeader("Authorization", "Bearer $token")
        when (method) {
            "GET" -> b.get()
            "POST" -> b.post((body ?: "{}").toRequestBody("application/json".toMediaType()))
            "PATCH" -> b.patch((body ?: "{}").toRequestBody("application/json".toMediaType()))
            "DELETE" -> b.delete()
            else -> b.get()
        }
        if (method == "POST" || method == "PATCH") {
            b.addHeader("Content-Type", "application/json")
        }
        return b.build()
    }

    data class HomeMember(
        val id: Int,
        val username: String,
        val email: String,
        val phone: String,
        val homeRole: String,
    )

    fun listMembers(context: Context): List<HomeMember> {
        val req = auth(context, "/api/home/members", "GET")
        return try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val arr = JSONArray(response.body?.string() ?: "[]")
                List(arr.length()) { i ->
                    val o = arr.getJSONObject(i)
                    HomeMember(
                        id = o.optInt("id", 0),
                        username = o.optString("username", ""),
                        email = o.optString("email", ""),
                        phone = o.optString("phone", ""),
                        homeRole = o.optString("home_role", "owner"),
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun updateMemberHomeRole(context: Context, memberId: Int, homeRole: String): Boolean {
        val body = JSONObject().apply { put("home_role", homeRole) }.toString()
        val req = auth(context, "/api/home/members/$memberId", "PATCH", body)
        return try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    fun removeMember(context: Context, memberId: Int): Boolean {
        val req = auth(context, "/api/home/members/$memberId", "DELETE")
        return try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    data class PendingDisarm(val id: String, val requestedByUserId: Int, val createdAt: Double)

    fun listPendingDisarmRequests(context: Context): List<PendingDisarm> {
        val req = auth(context, "/api/alarm/pending-disarm-requests", "GET")
        return try {
            client.newCall(req).execute().use { response ->
                if (!response.isSuccessful) return emptyList()
                val arr = JSONArray(response.body?.string() ?: "[]")
                List(arr.length()) { i ->
                    val o = arr.getJSONObject(i)
                    PendingDisarm(
                        id = o.optString("id", ""),
                        requestedByUserId = o.optInt("requested_by_user_id", 0),
                        createdAt = o.optDouble("created_at", 0.0),
                    )
                }
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun approveDisarm(context: Context, requestId: String): Boolean {
        val req = auth(context, "/api/alarm/disarm-requests/$requestId/approve", "POST", "{}")
        return try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    fun denyDisarm(context: Context, requestId: String): Boolean {
        val req = auth(context, "/api/alarm/disarm-requests/$requestId/deny", "POST", "{}")
        return try {
            client.newCall(req).execute().use { it.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }
}
