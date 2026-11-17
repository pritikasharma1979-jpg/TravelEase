import hashlib
import hmac
import secrets

from database import get_connection


def hash_password(password, salt=None):
    """Hash a password using PBKDF2 with a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        600_000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """Verify a password against its stored hash."""
    try:
        salt, expected_hash = stored_hash.split("$", 1)
        actual_hash = hash_password(password, salt).split("$", 1)[1]

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, AttributeError):
        return False


def register_user(username, password):
    """Register a new user in the database."""
    username = username.strip()

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if len(username) > 50:
        return False, "Username cannot exceed 50 characters."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    connection = get_connection()

    if connection is None:
        return False, "Cannot connect to the database."

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,)
        )

        if cursor.fetchone():
            return False, "This username is already registered."

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            """,
            (username, password_hash)
        )

        connection.commit()

        return True, "Account created successfully!"

    except Exception as error:
        connection.rollback()
        print(f"Registration error: {error}")
        return False, "Registration failed. Please try again."

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def login_user(username, password):
    """Authenticate a user and return their ID and username."""
    username = username.strip()

    connection = get_connection()

    if connection is None:
        return None

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id, username, password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cursor.fetchone()

        if user and verify_password(password, user[2]):
            return {
                "user_id": user[0],
                "username": user[1]
            }

        return None

    except Exception as error:
        print(f"Login error: {error}")
        return None

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()