import unittest
from unittest.mock import MagicMock, patch

import psycopg2

from db import addAvailableSystems
from db import connectMCtoAlarmSystem
from db import connectToAlarmSystem
from db import insertIntoDB


#test insertion into mock db
class TestCreateAlarmSystem(unittest.TestCase):
    #mock password generation
    @patch("db.addAvailableSystems.bcrypt.gensalt", return_value=b"salt")
    @patch("db.addAvailableSystems.bcrypt.hashpw", return_value=b"hashed_password")
    @patch("db.addAvailableSystems.generate_random_password", return_value="Pass12345678")
    def test_create_alarm_system_inserts_and_returns_id(
        self, _mock_password, _mock_hashpw, _mock_gensalt
    ):
        cursor = MagicMock()
        cursor.fetchone.return_value = [42]

        alarm_system_id, password = addAvailableSystems.create_alarm_system(cursor)

        self.assertEqual(alarm_system_id, 42)
        self.assertEqual(password, "Pass12345678")

        execute_args, execute_kwargs = cursor.execute.call_args
        self.assertIn("INSERT INTO alarm_system_table", execute_args[0])
        self.assertEqual(execute_args[1], ("hashed_password",))
        self.assertEqual(execute_kwargs, {})

#1 - test connection to microcontroller with normal variables
#2 - test connection to already connected microcontroller (should return false)
#3 - test connection to none alarm system (should return false)
class TestConnectMicroController(unittest.TestCase):

    
    @patch("db.connectMCtoAlarmSystem.connectToAlarmSystem.getCurrentAlarmSystemID", return_value=7)
    @patch("db.connectMCtoAlarmSystem.connectToDB.connectToDB")
    def test_connect_microcontroller_success(self, mock_connect_to_db, _mock_get_system_id):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect_to_db.return_value = conn

        result = connectMCtoAlarmSystem.connectMicroController(1001, "alice")

        self.assertTrue(result)
        cursor.execute.assert_called_once_with(
            "INSERT into microcontroller(microcontroller_id,alarm_system_id, current_state) VALUES(%s, %s, %s)",
            (1001, 7, "idle"),
        )
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    @patch("db.connectMCtoAlarmSystem.connectToAlarmSystem.getCurrentAlarmSystemID", return_value=7)
    @patch("db.connectMCtoAlarmSystem.connectToDB.connectToDB")
    def test_connect_microcontroller_rolls_back_on_insert_error(
        self, mock_connect_to_db, _mock_get_system_id
    ):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("insert failed")
        conn.cursor.return_value = cursor
        mock_connect_to_db.return_value = conn

        result = connectMCtoAlarmSystem.connectMicroController(1001, "alice")

        self.assertFalse(result)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()

    @patch("db.connectMCtoAlarmSystem.connectToAlarmSystem.getCurrentAlarmSystemID", return_value=None)
    @patch("db.connectMCtoAlarmSystem.connectToDB.connectToDB")
    def test_connect_microcontroller_returns_false_when_user_unpaired(
        self, mock_connect_to_db, _mock_get_system_id
    ):
        conn = MagicMock()
        mock_connect_to_db.return_value = conn

        result = connectMCtoAlarmSystem.connectMicroController(1001, "alice")

        self.assertFalse(result)
        conn.cursor.assert_not_called()
        conn.commit.assert_not_called()
        conn.rollback.assert_not_called()

#1 - test pairing of user to alarm system
#2 - test pairing to already paired system  
class TestConnectUserToSystem(unittest.TestCase):
    @patch("db.connectToAlarmSystem.addAvailableSystems.create_alarm_system", return_value=(11, "pw"))
    @patch("db.connectToAlarmSystem.connectToDB.connectToDB")
    @patch("db.connectToAlarmSystem.getCurrentAlarmSystemID", return_value=None)
    def test_connect_user_to_system_creates_and_pairs_when_unpaired(
        self, _mock_get_system_id, mock_connect_to_db, mock_create_alarm_system
    ):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect_to_db.return_value = conn

        connectToAlarmSystem.connectUserToSystem("alice")

        mock_create_alarm_system.assert_called_once_with(cursor)
        self.assertEqual(cursor.execute.call_count, 2)
        cursor.execute.assert_any_call(
            """
        UPDATE user_table
        SET alarm_system_id = %s
        WHERE username = %s
        """,
            (11, "alice"),
        )
        cursor.execute.assert_any_call(
            "UPDATE alarm_system_table SET paired = %s WHERE alarm_system_id = %s",
            ("T", 11),
        )
        conn.commit.assert_called_once()

    @patch("db.connectToAlarmSystem.connectToDB.connectToDB")
    @patch("db.connectToAlarmSystem.getCurrentAlarmSystemID", return_value=3)
    def test_connect_user_to_system_does_nothing_if_already_paired(
        self, _mock_get_system_id, mock_connect_to_db
    ):
        connectToAlarmSystem.connectUserToSystem("alice")

        mock_connect_to_db.assert_not_called()

#1 - test insertion of normal data in db
#2 - test insertion of duplicate username and alarm system id in db
class TestInsertUserInDB(unittest.TestCase):
    @patch("db.insertIntoDB.bcrypt.gensalt", return_value=b"salt")
    @patch("db.insertIntoDB.bcrypt.hashpw", return_value=b"hashed")
    @patch("db.insertIntoDB.connectToDB.connectToDB")
    def test_insert_user_commits_on_success(
        self, mock_connect_to_db, _mock_hashpw, _mock_gensalt
    ):
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_connect_to_db.return_value = conn

        user_info = ("alice", "alice@example.com", 5, "Secret123")
        result = insertIntoDB.insertUserInDB(user_info)

        self.assertIsNone(result)
        cursor.execute.assert_called_once_with(
            "INSERT into user_table(username, email, alarm_system_id, password_hash) VALUES(%s, %s, %s, %s)",
            user_info,
        )
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()
        conn.close.assert_called_once()

    @patch("db.insertIntoDB.bcrypt.gensalt", return_value=b"salt")
    @patch("db.insertIntoDB.bcrypt.hashpw", return_value=b"hashed")
    @patch("db.insertIntoDB.connectToDB.connectToDB")
    def test_insert_user_rolls_back_and_returns_false_on_integrity_error(
        self, mock_connect_to_db, _mock_hashpw, _mock_gensalt
    ):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = psycopg2.IntegrityError("duplicate key")
        conn.cursor.return_value = cursor
        mock_connect_to_db.return_value = conn

        user_info = ("alice", "alice@example.com", 5, "Secret123")
        result = insertIntoDB.insertUserInDB(user_info)

        self.assertFalse(result)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()
        conn.close.assert_called_once()