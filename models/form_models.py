from typing import Annotated

from fastapi import Form
from pydantic import BaseModel


class CreateQuizForm(BaseModel):
    q: str
    qn: int

    @property
    def prompt(self):
        return self.q

    @property
    def count(self):
        return self.qn

    @classmethod
    def form(cls, q: Annotated[str, Form()], qn: Annotated[int, Form()]):
        return cls(q=q, qn=qn)


class SubmitAnswerForm(BaseModel):
    option: int

    @classmethod
    def form(cls, option: Annotated[int, Form()]):
        return cls(option=option)


class GoToQuizForm(BaseModel):
    quiz_id: str

    @classmethod
    def form(cls, quiz_id: Annotated[str, Form()]):
        return cls(quiz_id=quiz_id)
