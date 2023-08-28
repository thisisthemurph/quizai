import asyncio
import os
from typing import Annotated

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, Form
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from quiz_builder import QuizBuilder

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


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


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", dict(request=request))


@app.post("/create", response_class=HTMLResponse)
async def create_quiz(request: Request, form: CreateQuizForm = Depends(CreateQuizForm.form)):
    builder = QuizBuilder(os.getenv("OPENAI_API_KEY"))
    quiz = builder.make_quiz(form.prompt, num_questions=form.count)

    ctx = dict(
        request=request,
        prompt=quiz.prompt,
        question=quiz.questions[0],
    )

    return templates.TemplateResponse("partials/question.html", ctx)


async def main():
    load_dotenv()
    config = uvicorn.Config("api:app", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
