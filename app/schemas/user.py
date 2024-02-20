from pydantic import BaseModel


class ResetPasswordInput(BaseModel):
    current_password: str
    new_password: str
