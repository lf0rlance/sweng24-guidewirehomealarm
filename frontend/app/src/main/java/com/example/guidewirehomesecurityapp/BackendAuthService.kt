package com.example.guidewirehomesecurityapp

import android.content.Context
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import kotlin.concurrent.thread

object BackendAuthService {

    fun verifyWithBackend(
        context: Context,
        idToken: String,
        onSuccess: () -> Unit,
        onError: () -> Unit
    ) {
        thread {
            try {
                val json = JSONObject()
                json.put("idToken", idToken)

                val body = json.toString()
                    .toRequestBody("application/json".toMediaType())

                println("Sending ID token to backend: $idToken")
                val request = Request.Builder()
                    .url("${BuildConfig.API_BASE_URL}auth/google")
                    .post(body)
                    .build()

                val response = OkHttpClient().newCall(request).execute()

                if (response.isSuccessful) {
                    onSuccess()
                } else {
                    onError()
                }
            } catch (e: Exception) {
                e.printStackTrace()
                onError()
            }
        }
    }
}
