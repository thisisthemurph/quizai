import psycopg2.extras
from result import Ok, Err, Result

from models import UserModel
from persistance.database import Database, DBSession


class UserRepo:
    def __init__(self, database: Database):
        self.database = database

    def get(self, email: str) -> Result[UserModel, str]:
        stmt = "SELECT id, name, email, password FROM users WHERE email = %s LIMIT 1;"

        with DBSession(self.database, psycopg2.extras.RealDictCursor) as db:
            db.cursor.execute(stmt, (email,))
            user_details = db.cursor.fetchone()

            if not user_details:
                return Err("A user with the email address could not be found")

            user = UserModel(
                id=user_details["id"],
                name=user_details["name"],
                email=user_details["email"],
                password=user_details["password"],
            )

            return Ok(user)

    def user_exists(self, email: str) -> Result[None, str]:
        stmt = """SELECT CASE WHEN COUNT(*) > 0 THEN true ELSE false END AS user_exists
                  FROM users u
                  WHERE u.email = %s
                  LIMIT 1"""

        with DBSession(self.database) as db:
            db.cursor.execute(stmt, (email,))
            exists = db.cursor.fetchone()[0]

            if exists:
                return Err("A user with the email address already exists")

            return Ok(None)

    def save(self, user: UserModel) -> None:
        stmt = """INSERT INTO users (name, email, password) VALUES (%s, %s, %s);"""

        with DBSession(self.database) as db:
            db.cursor.execute(stmt, (user.name, user.email, user.password))
            db.conn.commit()
