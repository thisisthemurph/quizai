from auth import Auth
from persistance.database import Database
from persistance.repositories import UserRepo, SessionRepo, QuizRepo


def auth_repo_param() -> Auth:
    db = Database.default()
    user_repo = UserRepo(db)
    session_repo = SessionRepo(db)
    return Auth(user_repo, session_repo)


def quiz_repo_param() -> QuizRepo:
    db = Database.default()
    return QuizRepo(db)
