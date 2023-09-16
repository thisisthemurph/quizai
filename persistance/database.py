import os
from typing import Type

import psycopg2
from psycopg2.extras import RealDictCursor, DictCursor
from psycopg2 import extensions
from dotenv import load_dotenv


class DatabaseConfig:
    def __init__(self, name: str, host: str, user: str, port: str, password: str):
        self.name = name
        self.host = host
        self.user = user
        self.port = port
        self.password = password

    @classmethod
    def default(cls):
        load_dotenv()
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_port = os.getenv("DB_PORT")
        db_password = os.getenv("DB_PASSWORD")

        return cls(db_name, db_host, db_user, db_port, db_password)


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config

    @classmethod
    def default(cls, create_tables: bool = False):
        config = DatabaseConfig.default()
        database = cls(config)

        if create_tables:
            database.create_tables_if_not_exists()

        return database

    @staticmethod
    def connect(config: DatabaseConfig = None) -> extensions.connection:
        config = config or DatabaseConfig.default()
        conn = psycopg2.connect(
            host=config.host,
            user=config.user,
            port=config.port,
            database=config.name,
            password=config.password,
        )

        return conn

    def create_tables_if_not_exists(self):
        create_uuid_extension = """CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""""

        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
        	id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        	name TEXT NOT NULL,
        	email TEXT NOT NULL,
        	password TEXT NOT NULL,
        	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );"""

        create_sessions_table = """
        CREATE TABLE IF NOT EXISTS sessions (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id uuid NOT NULL,
            login_time TIMESTAMP NOT NULL,
            expiration_time TIMESTAMP NOT NULL,
            ip_address VARCHAR(32),
            user_agent TEXT DEFAULT NULL,
            valid BOOL NOT NULL DEFAULT true,
            CONSTRAINT fk_users
                FOREIGN KEY(user_id)
                    REFERENCES users(id)
                        ON DELETE CASCADE
        );"""

        create_quizzes_table = """
        CREATE TABLE IF NOT EXISTS quizzes (
        	id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        	owner_id UUID,
        	prompt TEXT NOT NULL,
        	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        	CONSTRAINT fk_users
        		FOREIGN KEY (owner_id)
        			REFERENCES users(id)
        				ON DELETE SET NULL -- keep the quiz when the user is deleted
        );"""

        create_questions_table = """
        CREATE TABLE IF NOT EXISTS questions (
            id serial PRIMARY KEY,
            quiz_id uuid,
            text TEXT NOT NULL,
            CONSTRAINT fk_quizzes
                FOREIGN KEY(quiz_id)
                    REFERENCES quizzes(id)
                        ON DELETE CASCADE
        );"""

        create_options_table = """
        CREATE TABLE IF NOT EXISTS options (
            id serial PRIMARY KEY,
            question_id serial,
            text TEXT NOT NULL,
            correct BOOLEAN NOT NULL DEFAULT True,
            CONSTRAINT fk_questions
                FOREIGN KEY(question_id)
                    REFERENCES questions(id)
                        ON DELETE CASCADE
        );"""

        create_user_quiz_answers_table = """
        CREATE TABLE IF NOT EXISTS user_quiz_answers (
        	user_id UUID NOT NULL,
        	quiz_id UUID NOT NULL,
        	question_id INT NOT NULL,
        	correct BOOL NOT NULL,
        	CONSTRAINT fk_users
        		FOREIGN KEY(user_id)
        			REFERENCES users(id)
        				ON DELETE CASCADE,
        	CONSTRAINT fk_quizzes
        		FOREIGN KEY(quiz_id)
        			REFERENCES quizzes(id)
        				ON DELETE CASCADE,
        	CONSTRAINT fk_questions
        		FOREIGN KEY(question_id)
        			REFERENCES questions(id)
        				ON DELETE CASCADE
        );"""

        with DBSession(self) as db:
            db.cursor.execute(create_uuid_extension)
            db.cursor.execute(create_users_table)
            db.cursor.execute(create_sessions_table)
            db.cursor.execute(create_quizzes_table)
            db.cursor.execute(create_questions_table)
            db.cursor.execute(create_options_table)
            db.cursor.execute(create_user_quiz_answers_table)
            db.conn.commit()


class ConnectionCursor:
    def __init__(self, conn: extensions.connection, cursor: extensions.cursor):
        self.conn = conn
        self.cursor = cursor


class DBSession:
    def __init__(
        self, db: Database, cursor_factory: Type[RealDictCursor] | Type[DictCursor] | None = None
    ):
        self.db = db
        self.conn = None
        self.cursor = None
        self.cursor_factory = cursor_factory

    def __enter__(self):
        self.conn = self.db.connect()
        if self.cursor_factory is None:
            self.cursor = self.conn.cursor()
        else:
            self.cursor = self.conn.cursor(cursor_factory=self.cursor_factory)
        return ConnectionCursor(self.conn, self.cursor)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
        if self.cursor:
            self.cursor.close()
