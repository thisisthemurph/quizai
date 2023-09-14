import bcrypt


def hash_password(password: str) -> str:
    """Hashes a given password, returning the string representation of the hashed password"""
    return bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt(14)).decode("utf8")


def check_password(password: str, hashed_password: str) -> bool:
    """Compares a string representation of a password with a hashed version of the password.
    Returns True if matching, otherwise false."""
    return bcrypt.checkpw(password.encode("utf8"), hashed_password.encode("utf8"))
