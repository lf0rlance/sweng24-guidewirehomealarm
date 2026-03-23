package com.example.guidewirehomesecurityapp.auth

import android.content.Context
import android.content.SharedPreferences
import com.example.guidewirehomesecurityapp.BuildConfig
import kotlin.concurrent.thread
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

private const val PREFS_NAME = "auth_prefs"
private const val KEY_JWT = "jwt"

object BackendAuthService {

    private fun prefs(context: Context): SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** Persist JWT after successful sign-in/sign-up. */
    fun saveToken(context: Context, token: String) {
        prefs(context).edit().putString(KEY_JWT, token).apply()
    }

    /** Get stored JWT for authenticated API calls. Null if not logged in. */
    fun getToken(context: Context): String? =
        prefs(context).getString(KEY_JWT, null)?.takeIf { it.isNotBlank() }

    /** Clear stored JWT (e.g. on logout). */
    fun clearToken(context: Context) {
        prefs(context).edit().remove(KEY_JWT).apply()
    }

    private fun request(
        context: Context,
        path: String,
        idToken: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        thread {
            try {
                val json = JSONObject().apply { put("idToken", idToken) }
                val body = json.toString().toRequestBody("application/json".toMediaType())
                val base = BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")
                val url = "$base/api$path"
                android.util.Log.d("BackendAuth", "Request URL: $url")
                val request = Request.Builder()
                    .url(url)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .build()
                val client = OkHttpClient.Builder()
                    .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .writeTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                val response = client.newCall(request).execute()
                val responseBody = response.body?.string()
                if (response.isSuccessful) {
                    responseBody?.let { body ->
                        try {
                            val obj = JSONObject(body)
                            val jwt = obj.optString("token", "").takeIf { it.isNotBlank() }
                            if (jwt != null) {
                                saveToken(context, jwt)
                            }
                        } catch (_: Exception) { /* ignore parse failure */ }
                    }
                    android.os.Handler(android.os.Looper.getMainLooper()).post { onSuccess() }
                } else {
                    val errorMsg = try {
                        val errorJson = JSONObject(responseBody ?: "{}")
                        errorJson.optString("detail", errorJson.optString("error", "Unknown error"))
                    } catch (e: Exception) {
                        "HTTP ${response.code}: ${responseBody ?: "No response body"}"
                    }
                    val message = if (response.code == 404) {
                        "Backend route not found (404). Check that backend is running and URL is $url"
                    } else {
                        errorMsg
                    }
                    android.os.Handler(android.os.Looper.getMainLooper()).post { onError(message) }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                val message = when {
                    e is java.net.SocketTimeoutException || e is java.net.ConnectException ->
                        "Can't reach server. If using a physical device, set API_BASE_URL in frontend/local.properties to your PC's IP (e.g. http://192.168.0.x:5000/api/). 10.0.2.2 only works on the emulator."
                    else -> "Network error: ${e.message}"
                }
                android.os.Handler(android.os.Looper.getMainLooper()).post { onError(message) }
            }
        }
    }

    fun signUp(
        context: Context,
        idToken: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        request(context, "/auth/signup", idToken, onSuccess, onError)
    }

    fun signIn(
        context: Context,
        idToken: String,
        onMfaRequired: (String) -> Unit,   // passes email to show OTP screen
        onError: (String) -> Unit
    ) {
        thread {
            try {
                val json = JSONObject().apply { put("idToken", idToken) }
                val body = json.toString().toRequestBody("application/json".toMediaType())
                val base = BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")
                val url = "$base/api/auth/signin"
                val request = Request.Builder()
                    .url(url)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .build()
                val client = OkHttpClient.Builder()
                    .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                val response = client.newCall(request).execute()
                val responseBody = response.body?.string()
                if (response.isSuccessful) {
                    val obj = JSONObject(responseBody ?: "{}")
                    val email = obj.optString("email", "")
                    android.os.Handler(android.os.Looper.getMainLooper()).post {
                        onMfaRequired(email)
                    }
                } else {
                    val errorMsg = try {
                        JSONObject(responseBody ?: "{}").optString("detail", "Unknown error")
                    } catch (e: Exception) { "HTTP ${response.code}" }
                    android.os.Handler(android.os.Looper.getMainLooper()).post { onError(errorMsg) }
                }
            } catch (e: Exception) {
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    onError("Network error: ${e.message}")
                }
            }
        }
    }

    fun verifyOtp(
        context: Context,
        email: String,
        code: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        thread {
            try {
                val json = JSONObject().apply {
                    put("email", email)
                    put("code", code)
                }
                val body = json.toString().toRequestBody("application/json".toMediaType())
                val base = BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")
                val url = "$base/api/auth/verify-otp"
                val request = Request.Builder()
                    .url(url)
                    .post(body)
                    .addHeader("Content-Type", "application/json")
                    .build()
                val client = OkHttpClient.Builder()
                    .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                    .build()
                val response = client.newCall(request).execute()
                val responseBody = response.body?.string()
                if (response.isSuccessful) {
                    responseBody?.let {
                        val obj = JSONObject(it)
                        val jwt = obj.optString("token", "").takeIf { t -> t.isNotBlank() }
                        if (jwt != null) saveToken(context, jwt)
                    }
                    android.os.Handler(android.os.Looper.getMainLooper()).post { onSuccess() }
                } else {
                    val errorMsg = try {
                        JSONObject(responseBody ?: "{}").optString("detail", "Invalid code")
                    } catch (e: Exception) { "HTTP ${response.code}" }
                    android.os.Handler(android.os.Looper.getMainLooper()).post { onError(errorMsg) }
                }
            } catch (e: Exception) {
                android.os.Handler(android.os.Looper.getMainLooper()).post {
                    onError("Network error: ${e.message}")
                }
            }
        }
    }
}
