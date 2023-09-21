from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette import status

from auth import Auth
from persistance.database import Database
from persistance.repositories import UserRepo, SessionRepo
from routers.router_params import auth_repo_param


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


class SignInForm(BaseModel):
    email: str
    password: str

    @classmethod
    def form(
        cls,
        email: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ):
        return cls(email=email, password=password)

    def dict(self, **kwargs):
        return self.__dict__


router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="templates")


@router.get("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up_page(request: Request):
    ctx = dict(request=request)
    return templates.TemplateResponse("auth/sign_up.html", ctx)


@router.post("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up(
    request: Request,
    auth: Annotated[Auth, Depends(auth_repo_param)],
    form: SignUpForm = Depends(SignUpForm.form),
):
    result = auth.sign_up(**form.dict())

    if result.is_err():
        ctx = dict(request=request)
        return templates.TemplateResponse("auth/sign_up.html", ctx)

    return RedirectResponse("/auth/sign_in", status_code=status.HTTP_302_FOUND)


@router.get("/sign_in", response_class=HTMLResponse, tags=["auth"])
async def sign_in_page(request: Request, htmx: bool = False):
    ctx = dict(request=request)

    return (
        templates.TemplateResponse("auth/partials/sign_in_form.html", ctx)
        if htmx
        else templates.TemplateResponse("auth/sign_in.html", ctx)
    )


@router.post("/sign_in", response_class=HTMLResponse, tags=["auth"])
def sign_in(
    request: Request,
    auth: Annotated[Auth, Depends(auth_repo_param)],
    form: SignInForm = Depends(SignInForm.form),
):
    result = auth.sign_in(
        form.email,
        form.password,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
    )
    if result.is_err():
        raise HTTPException(status_code=400, detail=result.err_value or "Unable to sign in")

    user, session = result.ok_value
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="session",
        value=session.id,
        httponly=True,
        secure=False,
        max_age=15 * 60,
    )

    return response
