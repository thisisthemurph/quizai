from result import Ok, Result

import auth.cryptographic_fns as crypto
from models import UserModel
from persistance.database import DBSession, Database
from persistance.repositories.user_repo import UserRepo


class Auth:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

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
