import asyncio
import os
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import urllib.parse
from starlette import status

from persistance.database import Database
from persistance.quiz_repo import QuizRepo
from quiz_builder import QuizBuilder

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def quiz_repo_param() -> QuizRepo:
    db = Database.default()
    return QuizRepo(db)


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


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", dict(request=request))


@app.post("/create", response_class=HTMLResponse)
async def create_quiz(
        request: Request,
        quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)],
        form: CreateQuizForm = Depends(CreateQuizForm.form)):
    builder = QuizBuilder(os.getenv("OPENAI_API_KEY"))
    quiz = builder.make_quiz(form.prompt, num_questions=form.count)
    saved_quiz = quiz_repo.create(quiz)

    ctx = dict(request=request, quiz_id=saved_quiz.id, prompt=saved_quiz.prompt)
    return templates.TemplateResponse("partials/quiz-created.html", ctx)


@app.post("/find", response_class=HTMLResponse)
async def go_to_quiz(quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)], form: GoToQuizForm = Depends(GoToQuizForm.form)):
    quiz = quiz_repo.get(form.quiz_id)

    if quiz is None:
        message = urllib.parse.quote_plus("The quiz could not be found and may no longer exist.")
        return RedirectResponse(f"/not-found?message={message}", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(f"/quiz/{form.quiz_id}", status_code=status.HTTP_302_FOUND)


@app.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def get_quiz(request: Request, quiz_id: str, quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)]):
    quiz = quiz_repo.get(quiz_id)

    if quiz is None:
        message = urllib.parse.quote_plus("The quiz could not be found and may no longer exist.")
        return RedirectResponse(f"/not-found?message={message}")

    current_question = quiz_repo.get_current_question(quiz_id)
    counts = quiz_repo.get_results(quiz_id)

    ctx = dict(
        request=request,
        quiz=quiz,
        counts=counts,
        pct=int(counts.correct / len(quiz) * 100),
        current_question=current_question,
    )

    return templates.TemplateResponse("quiz-page.html", ctx)


@app.post("/quiz/{quiz_id}/{question_id}/submit", response_class=HTMLResponse)
async def submit_question_answer(
        request: Request,
        quiz_id: str,
        question_id: int,
        quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)],
        form: SubmitAnswerForm = Depends(SubmitAnswerForm.form)):
    quiz = quiz_repo.answer(quiz_id, question_id, form.option)
    current_question_index = quiz.get_question_index(question_id)
    counts = quiz_repo.get_results(quiz_id)
    quiz_completed = current_question_index == len(quiz) - 1

    if quiz_completed:
        ctx = dict(
            request=request,
            counts=counts,
            pct=int(counts.correct / len(quiz) * 100),
            question_count=len(quiz),
        )

        return templates.TemplateResponse("partials/quiz-completed-message.html", ctx)

    current_question = quiz.questions[current_question_index + 1]

    ctx = dict(
        request=request,
        quiz=quiz,
        counts=counts,
        pct=int(counts.correct / len(quiz) * 100),
        current_question=current_question,
    )

    return templates.TemplateResponse("partials/quiz-carousel.html", ctx)


@app.get("/not-found", response_class=HTMLResponse)
async def not_found(request: Request, message: str = None):
    ctx = dict(request=request, message=message or "The resource could not be found")
    return templates.TemplateResponse("not-found-page.html", ctx)


async def main():
    # Initialize the database for the initial run
    __db = Database.default()
    __db.create_tables_if_not_exists()

    config = uvicorn.Config("api:app", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
