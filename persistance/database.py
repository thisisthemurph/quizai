import os

import psycopg2
from psycopg2 import extensions
from dotenv import load_dotenv


class DatabaseConfig:
    def __init__(self, name: str, host: str, user: str, port: str, password: str):
        self.name = name
        self.host = host
        self.user = user
        self.port = port
        self.password = password


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    def connect(self) -> extensions.connection:
        load_dotenv()
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_port = os.getenv("DB_PORT")
        db_password = os.getenv("DB_PASSWORD")

        conn = psycopg2.connect(
            host=db_host,
            user=db_user,
            port=db_port,
            database=db_name,
            password=db_password,
        )

        return conn

    def connect_with_cursor(self) -> tuple[extensions.connection, extensions.cursor]:
        conn = self.connect()
        return conn, conn.cursor()


class ConnectionCursor:
    def __init__(self, conn: extensions.connection, cursor: extensions.cursor):
        self.conn = conn
        self.cursor = cursor


class DbConnection:
    def __init__(self, db: Database):
        self.db = db
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn, self.cursor = self.db.connect_with_cursor()
        return ConnectionCursor(self.conn, self.cursor)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        if self.cursor:
            self.cursor.close()


def init():
    load_dotenv()
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_port = os.getenv("DB_PORT")
    db_password = os.getenv("DB_PASSWORD")

    config = DatabaseConfig(db_name, db_host, db_user, db_port, db_password)
    return Database(config)
