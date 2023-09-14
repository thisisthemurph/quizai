from pydantic import BaseModel


class UserModel(BaseModel):
    id: str | None = None
    email: str
    name: str
    password: str
    is_admin: bool = False

    def __str__(self):
        return self.email

    def __repr__(self):
        return f"User(name={self.name}, email={self.email})"
