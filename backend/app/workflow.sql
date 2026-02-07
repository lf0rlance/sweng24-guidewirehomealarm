--User table:
CREATE TABLE user_table (
  id INT PRIMARY KEY,
  username VARCHAR(100) UNIQUE,
  email VARCHAR(255) UNIQUE,
  alarm_system_id INT,
  password_hash TEXT NOT NULL
);


--Alarm system table
CREATE TABLE alarm_system (
  alarm_system_id INT PRIMARY KEY,
  system_password_hash TEXT NOT NULL,
  armed BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE user_table
ADD FOREIGN KEY (alarm_system_id)
REFERENCES alarm_system (alarm_system_id)
ON DELETE SET NULL;

--micro controller table
CREATE TABLE microcontroller (
  microcontroller_id INT PRIMARY KEY,
  alarm_system_id INT NOT NULL,
  current_state TEXT NOT NULL,
  FOREIGN KEY (alarm_system_id)
    REFERENCES alarm_system (alarm_system_id)
    ON DELETE CASCADE
);