import auth.cryptographic_fns as crypto
from models import UserModel
from persistance.repositories import user_repo
from auth.exceptions import UserAlreadyExistsException


class Auth:
    @staticmethod
    def sign_up(name: str, email: str, password: str):
        existing_user, error = user_repo.user_exists(email=email)
        if existing_user:
            raise UserAlreadyExistsException(error)

        user = UserModel(name=name, email=email, password=crypto.hash_password(password))

        # TODO: Save the user

        return user
