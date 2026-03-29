package com.example.guidewirehomesecurityapp.api

/**
 * Processed sensor event from the backend (ESP32 → backend → app).
 * Backend validates: device_id (esp32_xxxx), event_type, count, timestamp.
 */
data class SensorEvent(
    val device_id: String,
    val event_type: String,
    val count: Int,
    val timestamp: Double,
    /** mA for [current_power_usage] events when backend stores it */
    val value: Double? = null,
) {
    /** Human-readable label for event_type (e.g. door_open → "Door opened") */
    fun displayType(): String = when (event_type) {
        "door_open" -> "Door opened"
        "door_closed" -> "Door closed"
        "door_open_2" -> "Sensor 2 opened"
        "door_closed_2" -> "Sensor 2 closed"
        "alarm_enabled" -> "Alarm armed"
        "alarm_disabled" -> "Alarm disarmed"
        "led_toggle" -> "Sensor toggled"
        else -> event_type
    }
}
