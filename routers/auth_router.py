from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette import status

from auth.exceptions import UserAlreadyExistsException
from auth import Auth


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


@router.get("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up_page(request: Request):
    ctx = dict(request=request)
    return templates.TemplateResponse("auth/sign_up.html", ctx)


@router.post("/sign_up", response_class=HTMLResponse, tags=["auth"])
async def sign_up(request: Request, form: SignUpForm = Depends(SignUpForm.form)):
    try:
        Auth.sign_up(**form.dict())
    except UserAlreadyExistsException as ex:
        ctx = dict(request=request)
        return templates.TemplateResponse("auth/sign_up.html", ctx)

    return RedirectResponse("/auth/sign_in", status_code=status.HTTP_302_FOUND)


@router.get("/sign_in", response_class=HTMLResponse, tags=["auth"])
async def sign_in_page(request: Request):
    ctx = dict(request=request)
    return templates.TemplateResponse("auth/sign_in.html", ctx)
