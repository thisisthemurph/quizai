import bcrypt
from result import Ok, Err, Result

import auth.cryptographic_fns as crypto
from models import UserModel, SessionModel
from persistance.database import Database
from persistance.repositories import UserRepo, SessionRepo


class Auth:
    def __init__(self, user_repo: UserRepo, session_repo: SessionRepo):
        self.user_repo = user_repo
        self.session_repo = session_repo

    @property
    def database(self) -> Database:
        return self.user_repo.database

    def sign_up(self, name: str, email: str, password: str) -> Result[UserModel, str]:
        result = self.user_repo.user_exists(email=email)
        if result.is_err():
            return result

        user = UserModel(name=name, email=email, password=crypto.hash_password(password))
        self.user_repo.save(user)

        return Ok(user)

    def sign_in(
        self, email: str, password: str, ip_address=None, user_agent=None
    ) -> Result[tuple[UserModel, SessionModel], str]:
        generic_auth_err = "Email and password combination does not match any users"

        user_result = self.user_repo.get_by_email(email)

        if user_result.is_err():
            return user_result

        user: UserModel = user_result.ok_value
        encoded_pw = password.encode("utf8")
        encoded_user_pw = user.password.encode("utf8")

        match = bcrypt.checkpw(encoded_pw, encoded_user_pw)
        if not match:
            return Err(generic_auth_err)

        # TODO: Create a session in the session table
        # TODO: Pass in the ip address and user agent
        session_result = self.session_repo.create(user.id, ip_address, user_agent)
        if session_result.is_err():
            return session_result

        session: SessionModel = session_result.ok_value
        return Ok((user, session))
