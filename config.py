import mysql.connector


def get_db_connection():
    configs = [
        {"host": "localhost", "user": "root", "password": "", "database": "getpassdb"},
        {"host": "localhost", "user": "root", "password": "Baskar@123", "database": "getpassdb"},
        {"host": "localhost", "user": "sample", "password": "Baskar@123", "database": "getpassdb"},
    ]

    last_error = None
    for config in configs:
        try:
            return mysql.connector.connect(**config)
        except mysql.connector.Error as exc:
            last_error = exc

    if last_error:
        raise last_error

    raise RuntimeError("MySQL connection configuration is missing.")