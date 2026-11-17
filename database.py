import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Pahilove@7",
    "database": "travelease_db",
}


def get_connection():
    """Create and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as error:
        print(f"MySQL connection failed: {error}")

    return None


def test_connection():
    """Test the TravelEase database connection."""
    connection = get_connection()

    if connection is None:
        print("Database connection unsuccessful.")
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        print(f"Connected successfully to database: {result[0]}")
        return True

    except Error as error:
        print(f"Database test failed: {error}")
        return False

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


if __name__ == "__main__":
    test_connection()