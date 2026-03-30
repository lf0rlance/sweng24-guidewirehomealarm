package com.example.guidewirehomesecurityapp.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.example.guidewirehomesecurityapp.MainActivity
import com.example.guidewirehomesecurityapp.api.BackendEndpointResolver
import com.example.guidewirehomesecurityapp.auth.BackendAuthService
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlin.concurrent.thread
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Handles FCM tokens and incoming push notifications for sensor events (door open/close).
 */
class AlarmFirebaseMessagingService : FirebaseMessagingService() {

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        registerTokenWithBackend(this, token)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        val title = message.notification?.title ?: message.data["title"] ?: "Sensor event"
        val body = message.notification?.body ?: message.data["body"] ?: message.data["device_id"] ?: ""
        showNotification(title, body)
    }

    private fun showNotification(title: String, body: String) {
        val channelId = CHANNEL_ID
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Sensor events",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply { description = "Door and sensor events" }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
        val intent = Intent(this, MainActivity::class.java).apply { flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP }
        val pending = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setContentIntent(pending)
            .setAutoCancel(true)
            .build()
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        nm.notify(NOTIFICATION_ID, notification)
    }

    companion object {
        private const val CHANNEL_ID = "sensor_events"
        private const val NOTIFICATION_ID = 1

        private val client = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()

        private const val TAG = "FCMRegister"

        /**
         * Call right after login so this device's FCM token is associated with the user who just signed in.
         * Fetches current FCM token and registers it with the backend (JWT is already saved).
         */
        fun registerTokenAfterLogin(context: Context) {
            val appContext = context.applicationContext
            FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
                if (!task.isSuccessful) {
                    android.util.Log.w(TAG, "FCM token not ready: ${task.exception?.message}")
                    return@addOnCompleteListener
                }
                val token = task.result ?: return@addOnCompleteListener
                android.util.Log.d(TAG, "Registering FCM token after login (preview ...${token.takeLast(8)})")
                registerTokenWithBackend(appContext, token)
            }
        }

        /**
         * Register FCM token with backend for the current user's alarm system.
         * Requires user to be logged in (JWT). Use applicationContext so it works after navigation.
         */
        fun registerTokenWithBackend(context: Context, token: String) {
            thread {
                try {
                    val appContext = context.applicationContext
                    val jwt = BackendAuthService.getToken(appContext)
                    if (jwt.isNullOrBlank()) {
                        android.util.Log.w(TAG, "FCM register: no JWT (not logged in?), skipping")
                        return@thread
                    }
                    val base = BackendEndpointResolver.apiBaseUrl(appContext)
                    val url = "$base/api/notifications/register"
                    val body = JSONObject().apply { put("token", token) }.toString()
                        .toRequestBody("application/json".toMediaType())
                    val request = Request.Builder()
                        .url(url)
                        .post(body)
                        .addHeader("Content-Type", "application/json")
                        .addHeader("Authorization", "Bearer $jwt")
                        .build()
                    val response = client.newCall(request).execute()
                    if (response.isSuccessful) {
                        android.util.Log.d(TAG, "FCM register: ok (${response.code})")
                    } else {
                        android.util.Log.e(TAG, "FCM register: failed ${response.code} ${response.body?.string()?.take(200)}")
                    }
                } catch (e: Exception) {
                    android.util.Log.e(TAG, "FCM register: error", e)
                }
            }
        }
    }
}
