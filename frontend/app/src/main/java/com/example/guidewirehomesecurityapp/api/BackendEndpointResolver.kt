package com.example.guidewirehomesecurityapp.api

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import com.example.guidewirehomesecurityapp.BuildConfig
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import java.net.Inet4Address
import java.net.NetworkInterface
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Resolves backend URL dynamically on local Wi-Fi/hotspot networks.
 *
 * Behavior:
 * - Uses API_BASE_URL from local.properties as fallback.
 * - Tries previously discovered host first (per subnet).
 * - If unreachable, scans current /24 subnet for /health on same port.
 */
object BackendEndpointResolver {
    private const val TAG = "BackendEndpointResolver"
    private const val PREFS_NAME = "backend_endpoint_prefs"
    private const val KEY_HOST = "host"
    private const val KEY_SUBNET = "subnet"
    private const val SCAN_THREADS = 48

    @Volatile private var cachedApiBase: String? = null

    private val probeClient = OkHttpClient.Builder()
        .connectTimeout(1200, TimeUnit.MILLISECONDS)
        .readTimeout(1200, TimeUnit.MILLISECONDS)
        .writeTimeout(1200, TimeUnit.MILLISECONDS)
        .build()

    fun apiBaseUrl(context: Context): String {
        cachedApiBase?.let {
            if (isHealthy(it)) return it
            cachedApiBase = null
        }

        val fallbackApi = BuildConfig.API_BASE_URL.trimEnd('/').removeSuffix("/api")
        val fallbackHttp = fallbackApi.toHttpUrlOrNull() ?: return fallbackApi
        val subnetPrefix = currentSubnetPrefix(context)

        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val rememberedHost = prefs.getString(KEY_HOST, null)
        val rememberedSubnet = prefs.getString(KEY_SUBNET, null)

        if (!subnetPrefix.isNullOrBlank() && rememberedHost != null && rememberedSubnet == subnetPrefix) {
            val rememberedBase = buildBase(fallbackHttp, rememberedHost)
            if (isHealthy(rememberedBase)) {
                cachedApiBase = rememberedBase
                Log.d(TAG, "Using remembered backend host: $rememberedBase")
                return rememberedBase
            }
        }

        if (isHealthy(fallbackApi)) {
            cachedApiBase = fallbackApi
            Log.d(TAG, "Using fallback backend host from BuildConfig: $fallbackApi")
            return fallbackApi
        }

        if (!subnetPrefix.isNullOrBlank()) {
            discoverInSubnet(context, subnetPrefix, fallbackHttp)?.let { discoveredBase ->
                val host = discoveredBase.toHttpUrlOrNull()?.host
                if (!host.isNullOrBlank()) {
                    prefs.edit()
                        .putString(KEY_HOST, host)
                        .putString(KEY_SUBNET, subnetPrefix)
                        .apply()
                }
                cachedApiBase = discoveredBase
                Log.d(TAG, "Discovered backend host dynamically: $discoveredBase")
                return discoveredBase
            }
        }

        cachedApiBase = fallbackApi
        Log.w(TAG, "Backend discovery failed; falling back to BuildConfig host: $fallbackApi")
        return fallbackApi
    }

    fun imageBaseUrl(context: Context): String {
        val fallbackImage = BuildConfig.IMAGE_BASE_URL.trimEnd('/')
        val imageHttp = fallbackImage.toHttpUrlOrNull() ?: return fallbackImage
        val apiHttp = apiBaseUrl(context).toHttpUrlOrNull() ?: return fallbackImage
        return imageHttp.newBuilder()
            .scheme(apiHttp.scheme)
            .host(apiHttp.host)
            .port(apiHttp.port)
            .build()
            .toString()
            .trimEnd('/')
    }

    private fun discoverInSubnet(
        context: Context,
        subnetPrefix: String,
        fallbackHttp: okhttp3.HttpUrl
    ): String? {
        val ownIp = currentIpv4Address(context)
        val ownLastOctet = ownIp?.substringAfterLast('.')?.toIntOrNull()

        val pool = Executors.newFixedThreadPool(SCAN_THREADS)
        return try {
            val completion = java.util.concurrent.ExecutorCompletionService<String?>(pool)
            var taskCount = 0
            for (hostOctet in 1..254) {
                if (hostOctet == ownLastOctet) continue
                val host = "$subnetPrefix.$hostOctet"
                completion.submit(Callable {
                    val candidateBase = buildBase(fallbackHttp, host)
                    if (isHealthy(candidateBase)) candidateBase else null
                })
                taskCount++
            }

            repeat(taskCount) {
                val found = completion.take().get()
                if (found != null) return found
            }
            null
        } catch (_: Exception) {
            null
        } finally {
            pool.shutdownNow()
        }
    }

    private fun isHealthy(base: String): Boolean {
        val request = Request.Builder()
            .url("${base.trimEnd('/')}/health")
            .get()
            .build()
        return try {
            probeClient.newCall(request).execute().use { response -> response.isSuccessful }
        } catch (_: Exception) {
            false
        }
    }

    private fun buildBase(fallbackHttp: okhttp3.HttpUrl, host: String): String =
        fallbackHttp.newBuilder()
            .host(host)
            .build()
            .toString()
            .trimEnd('/')
            .removeSuffix("/api")

    private fun currentSubnetPrefix(context: Context): String? =
        currentIpv4Address(context)
            ?.split('.')
            ?.takeIf { it.size == 4 }
            ?.take(3)
            ?.joinToString(".")

    private fun currentIpv4Address(context: Context): String? {
        val fromActiveNetwork = try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val active = cm.activeNetwork ?: return fallbackIpv4Address()
            val props = cm.getLinkProperties(active) ?: return fallbackIpv4Address()
            props.linkAddresses
                .asSequence()
                .mapNotNull { it.address as? Inet4Address }
                .map { it.hostAddress }
                .firstOrNull { ip ->
                    ip != null &&
                        !ip.startsWith("127.") &&
                        !ip.startsWith("169.254.")
                }
        } catch (_: Exception) {
            null
        }
        if (fromActiveNetwork != null) return fromActiveNetwork

        // If active network points elsewhere (e.g. cellular), prefer any Wi-Fi transport network.
        val fromWifiNetwork = try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            cm.allNetworks
                .asSequence()
                .filter { network ->
                    cm.getNetworkCapabilities(network)
                        ?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true
                }
                .mapNotNull { network ->
                    cm.getLinkProperties(network)
                        ?.linkAddresses
                        ?.asSequence()
                        ?.mapNotNull { it.address as? Inet4Address }
                        ?.map { it.hostAddress }
                        ?.firstOrNull { ip ->
                            ip != null &&
                                !ip.startsWith("127.") &&
                                !ip.startsWith("169.254.")
                        }
                }
                .firstOrNull()
        } catch (_: Exception) {
            null
        }
        return fromWifiNetwork ?: fallbackIpv4Address()
    }

    private fun fallbackIpv4Address(): String? {
        return try {
            val interfaces = NetworkInterface.getNetworkInterfaces()?.toList().orEmpty()
            interfaces
                .asSequence()
                .filter { !it.isLoopback && it.isUp }
                .flatMap { it.inetAddresses.toList().asSequence() }
                .filterIsInstance<Inet4Address>()
                .map { it.hostAddress }
                .firstOrNull { ip ->
                    ip != null &&
                        !ip.startsWith("127.") &&
                        !ip.startsWith("169.254.")
                }
        } catch (_: Exception) {
            null
        }
    }
}
