from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette import status

from auth import Auth
from persistance.database import Database
from persistance.repositories.user_repo import UserRepo


class SignUpForm(BaseModel):
    name: str
    email: str
    password: str

    @classmethod
    def form(
        cls,
        name: Annotated[str, Form()],
        email: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ):
        return cls(name=name, email=email, password=password)

    def dict(self, **kwargs):
        return self.__dict__


router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="templates")


def auth_repo_param() -> Auth:
    db = Database.default()
    user_repo = UserRepo(db)
    return Auth(user_repo)


@router.get("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up_page(request: Request):
    ctx = dict(request=request)
    return templates.TemplateResponse("auth/sign_up.html", ctx)


@router.post("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up(
        request: Request,
        auth: Annotated[Auth, Depends(auth_repo_param)],
        form: SignUpForm = Depends(SignUpForm.form)):
    result = auth.sign_up(**form.dict())

    if result.is_err():
        ctx = dict(request=request)
        return templates.TemplateResponse("auth/sign_up.html", ctx)

    return RedirectResponse("/auth/sign_in", status_code=status.HTTP_302_FOUND)


@router.get("/sign_in", response_class=HTMLResponse, tags=["auth"])
async def sign_in_page(request: Request):
    ctx = dict(request=request)
    return templates.TemplateResponse("auth/sign_in.html", ctx)
