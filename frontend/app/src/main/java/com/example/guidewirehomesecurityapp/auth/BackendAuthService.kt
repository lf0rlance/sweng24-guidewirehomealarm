package com.example.guidewirehomesecurityapp.auth

import android.content.Context
import com.example.guidewirehomesecurityapp.BuildConfig
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import kotlin.concurrent.thread

object BackendAuthService {

    private fun request(
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
        request("/auth/signup", idToken, onSuccess, onError)
    }

    fun signIn(
        context: Context,
        idToken: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        request("/auth/signin", idToken, onSuccess, onError)
    }
}
