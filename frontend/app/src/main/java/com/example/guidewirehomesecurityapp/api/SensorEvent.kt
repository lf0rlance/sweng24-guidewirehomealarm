package com.example.guidewirehomesecurityapp.api

/**
 * Processed sensor event from the backend (ESP32 → backend → app).
 * Backend validates: device_id (esp32_xxxx), event_type, count, timestamp.
 */
data class SensorEvent(
    val device_id: String,
    val event_type: String,
    val count: Int,
    val timestamp: Double
) {
    /** Human-readable label for event_type (e.g. door_open → "Door opened") */
    fun displayType(): String = when (event_type) {
        "door_open" -> "Door opened"
        "door_closed" -> "Door closed"
        "alarm_enabled" -> "Alarm enabled"
        "alarm_disabled" -> "Alarm disabled"
        else -> event_type
    }
}
