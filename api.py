import asyncio
import os
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Depends, Cookie
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import urllib.parse
from starlette import status

import routers
from models import UserModel
from models.form_models import CreateQuizForm, SubmitAnswerForm, GoToQuizForm
from persistance.database import Database

from persistance.repositories import QuizRepo, SessionRepo, UserRepo
from quiz_builder import QuizBuilder
from routers.router_params import quiz_repo_param, auth_repo_param

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.middleware("http")
async def ansure_current_user_middleware(request: Request, call_next):
    """Ensures there is a current_user object on the request state"""
    request.state.current_user = None
    session_id = request.cookies.get("session")

    if session_id:
        database = Database.default()
        user_repo = UserRepo(database)
        result = user_repo.get_by_session(session_id)

        if result.is_ok():
            request.state.current_user = result.ok_value

    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Renders the home page."""
    return templates.TemplateResponse("index.html", dict(request=request))


@app.post("/create", response_class=HTMLResponse)
async def create_quiz(
    request: Request,
    quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)],
    form: CreateQuizForm = Depends(CreateQuizForm.form),
):
    """Creates a new quiz and presents the button to start the quiz."""
    builder = QuizBuilder(os.getenv("OPENAI_API_KEY"))
    quiz = builder.make_quiz(form.prompt, num_questions=form.count)

    user_id = request.state.current_user.id if request.state.current_user else None
    saved_quiz = quiz_repo.create(quiz, user_id)

    ctx = dict(request=request, quiz_id=saved_quiz.id, prompt=saved_quiz.prompt)
    return templates.TemplateResponse("partials/quiz-created.html", ctx)


@app.post("/find", response_class=HTMLResponse)
async def go_to_quiz(
    quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)],
    form: GoToQuizForm = Depends(GoToQuizForm.form),
):
    """Finsd a given quiz and redirects to it if found, otherwise redirects to error page."""
    quiz = quiz_repo.get(form.quiz_id)

    if quiz is None:
        message = urllib.parse.quote_plus("The quiz could not be found and may no longer exist.")
        return RedirectResponse(f"/not-found?message={message}", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(f"/quiz/{form.quiz_id}", status_code=status.HTTP_302_FOUND)


@app.get("/quiz/{quiz_id}", response_class=HTMLResponse)
async def get_quiz(
    request: Request, quiz_id: str, quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)]
):
    """Returns the requested quiz."""
    quiz = quiz_repo.get(quiz_id)

    if quiz is None:
        message = urllib.parse.quote_plus("The quiz could not be found and may no longer exist.")
        return RedirectResponse(f"/not-found?message={message}")

    # TODO: Maybe this only needs to get the ID of the current question?
    current_question = quiz_repo.get_current_question(quiz_id)
    current_question_index = quiz.get_question_index(current_question.id)
    counts = quiz_repo.get_results(quiz_id)

    ctx = dict(
        request=request,
        quiz=quiz,
        counts=counts,
        pct=int(counts.correct / len(quiz) * 100),
        question=quiz.questions[current_question_index],
        question_number=current_question_index + 1,
    )

    return templates.TemplateResponse("quiz-page.html", ctx)


@app.get("/quiz/{quiz_id}/next", response_class=HTMLResponse)
async def get_quiz(
    request: Request, quiz_id: str, quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)]
):
    """Returns the next question for the given quiz, or the quiz complete notification if complete."""
    quiz = quiz_repo.get(quiz_id)
    if quiz is None:
        message = urllib.parse.quote_plus("The quiz could not be found and may no longer exist.")
        return RedirectResponse(f"/not-found?message={message}")

    # TODO: Maybe this only needs to get the ID of the current question?
    current_question = quiz_repo.get_current_question(quiz_id)
    if current_question is None:
        counts = quiz_repo.get_results(quiz_id)
        ctx = dict(
            request=request,
            counts=counts,
            pct=int(counts.correct / len(quiz) * 100),
            question_count=len(quiz),
        )

        return templates.TemplateResponse("partials/quiz-completed-message.html", ctx)

    current_question_index = quiz.get_question_index(current_question.id)
    counts = quiz_repo.get_results(quiz_id)

    ctx = dict(
        request=request,
        quiz=quiz,
        counts=counts,
        pct=int(counts.correct / len(quiz) * 100),
        question=quiz.questions[current_question_index],
        question_number=current_question_index + 1,
    )

    return templates.TemplateResponse("partials/question.html", ctx)


@app.post("/quiz/{quiz_id}/{question_id}/submit", response_class=HTMLResponse)
async def submit_question_answer(
    request: Request,
    quiz_id: str,
    question_id: int,
    quiz_repo: Annotated[QuizRepo, Depends(quiz_repo_param)],
    form: SubmitAnswerForm = Depends(SubmitAnswerForm.form),
):
    """Updates the answer for the question and returns the next question in the list."""
    current_user: UserModel = request.state.current_user

    quiz = quiz_repo.get(quiz_id)
    answered_correctly = quiz_repo.answer(quiz_id, question_id, form.option, current_user.id)
    current_question_index = quiz.get_question_index(question_id)
    next_question_index = current_question_index + 1
    counts = quiz_repo.get_results(quiz_id)
    quiz_completed = current_question_index == len(quiz) - 1

    if not answered_correctly:
        current_question = quiz.questions[current_question_index]
        ctx = dict(request=request, quiz_id=quiz_id, correct_answer=current_question.correct_answer)
        return templates.TemplateResponse("partials/incorrect.html", ctx)

    if quiz_completed:
        ctx = dict(
            request=request,
            counts=counts,
            pct=int(counts.correct / len(quiz) * 100),
            question_count=len(quiz),
        )

        return templates.TemplateResponse("partials/quiz-completed-message.html", ctx)

    ctx = dict(
        request=request,
        quiz=quiz,
        counts=counts,
        pct=int(counts.correct / len(quiz) * 100),
        question=quiz.questions[next_question_index],
        question_number=next_question_index + 1,
    )

    return templates.TemplateResponse("partials/question.html", ctx)


@app.get("/not-found", response_class=HTMLResponse)
async def not_found(request: Request, message: str = None):
    ctx = dict(request=request, message=message or "The resource could not be found")
    return templates.TemplateResponse("not-found-page.html", ctx)


app.include_router(routers.auth_router)


async def main():
    # This is for development purposes only
    # Initialize the database for the initial run
    __db = Database.default()
    __db.create_tables_if_not_exists()

    config = uvicorn.Config("api:app", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
