import psycopg2.extras
from result import Ok, Err, Result
from datetime import datetime, timedelta

from models import SessionModel
from persistance.database import Database, DBSession


class SessionRepo:
    def __init__(self, database: Database):
        self.database = database

    def get(self, session_id: str) -> Result[SessionModel, str]:
        stmt = "SELECT id, user_id, login_time, expiration_time, ip_address, user_agent, valid FROM sessions WHERE id = %s"

        with DBSession(self.database, psycopg2.extras.RealDictCursor) as db:
            db.cursor.execute(stmt, (session_id,))
            session_data = db.cursor.fetchone()

            if not session_data:
                return Err("The user has no current sessions")

            session = SessionModel(
                id=session_data["id"],
                user_id=session_data["user_id"],
                login_time=session_data["login_time"],
                expiration_time=session_data["expiration_time"],
                ip_address=session_data["ip_address"],
                user_agent=session_data["user_agent"],
                valid=session_data["valid"],
            )

            return Ok(session)

    def create(self, user_id: str, ip_address: str, user_agent: str) -> Result[SessionModel, str]:
        stmt = """
        INSERT INTO sessions (user_id, login_time, expiration_time, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;"""

        with DBSession(self.database) as db:
            db.cursor.execute(
                stmt, (user_id, datetime.now(), datetime.now(), ip_address, user_agent)
            )
            session_id: str = db.cursor.fetchone()[0]
            db.conn.commit()

            return self.get(session_id)
