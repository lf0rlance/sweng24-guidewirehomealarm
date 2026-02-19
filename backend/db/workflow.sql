--database name: alarm_system 

--User table:
CREATE TABLE user_table (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  alarm_system_id INT,
  password_hash TEXT NOT NULL,
  role VARCHAR(20),
  CHECK (role IN ('admin', 'user'))
);

--Alarm system table
CREATE TABLE alarm_system_table (
  alarm_system_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  system_password_hash TEXT NOT NULL,
  armed BOOLEAN NOT NULL DEFAULT FALSE,
  paired BOOLEAN NOT NULL DEFAULT FALSE
);

--micro controller table
CREATE TABLE microcontroller (
  microcontroller_id INT PRIMARY KEY,
  alarm_system_id INT NOT NULL,
  current_state TEXT NOT NULL,
  FOREIGN KEY (alarm_system_id)
    REFERENCES alarm_system_table (alarm_system_id)
    ON DELETE CASCADE
);

-- FCM push tokens (one token per device; re-registering updates alarm_system_id)
CREATE TABLE IF NOT EXISTS fcm_tokens (
  token TEXT PRIMARY KEY,
  alarm_system_id INT NOT NULL,
  FOREIGN KEY (alarm_system_id) REFERENCES alarm_system_table (alarm_system_id) ON DELETE CASCADE
);