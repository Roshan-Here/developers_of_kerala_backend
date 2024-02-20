from fastapi import APIRouter, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from app.core.security import (
    pwd_context,
    create_access_token,
    blacklist_token,
    verify_refresh_token,
    create_access_token,
    generate_refresh_token,
)
from app.api.deps import oauth2_scheme , get_current_user
from app.db.engine import db
from app.schemas.user import ResetPasswordInput
from bson import ObjectId
from jose import JWTError

router = APIRouter()
token_router = APIRouter()


@router.post(
    "/register",
    responses={
        200: {
            "description": "Successful Registration",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User registered successfully",
                        "user_id": "string",
                    }
                }
            },
        },
        500: {
            "description": "Failed to register user",
            "content": {
                "application/json": {"example": {"detail": "Failed to register user"}}
            },
        },
    },
)
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(
        ...,
        choices=["company", "developer"],
        description="User role - valid options: 'company', 'developer'",
    ),
) -> JSONResponse:
    """
    Register a new user.

    Args:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password of the user.
        role (str): The role of the user - valid options : 'developer' 'company'

    Returns:
        JSONResponse: A JSON response containing the message and user_id if the user is registered successfully.

    Raises:
        HTTPException: If failed to register the user.
    """
    print("role----", role)
    if role not in ["company", "developer"]:
        raise HTTPException(status_code=422, detail="Invalid role")
    existing_company_user = db.Company.find_one(
        {"$or": [{"username": username}, {"email": email}]}
    )
    existing_developer_user = db.Developers.find_one(
        {"$or": [{"username": username}, {"email": email}]}
    )

    if existing_company_user or existing_developer_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user_dict = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    }
    user_dict["password"] = pwd_context.hash(user_dict["password"])

    # Choose the collection based on the role
    if role == "company":
        result = db.Company.insert_one(user_dict)
    elif role == "developer":
        result = db.Developers.insert_one(user_dict)

    if result.acknowledged:
        return JSONResponse(
            status_code=200,
            content={
                "message": "User registered successfully",
            },
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to register user")


@router.post(
    "/token",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "string",
                        "token_type": "string",
                        "role": "string",
                        "username": "string",
                    }
                }
            },
        },
        400: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials"}}
            },
        },
    },
)
async def login(username: str = Form(...), password: str = Form(...)) -> JSONResponse:
    """
    login a user.
    Generate an access token for the user based on their username or email and password.

    Args:
        username_or_email (str): The username or email of the user.
        password (str): The password of the user.

    Returns:
        JSONResponse: A JSON response containing the access token, token type, role, and username.

    Raises:
        HTTPException: If the provided credentials are invalid.
    """
    user_in_company = db.Company.find_one(
        {"$or": [{"username": username}, {"email": username}]}
    )
    user_in_developers = db.Developers.find_one(
        {"$or": [{"username": username}, {"email": username}]}
    )

    user = user_in_company or user_in_developers
    if user and pwd_context.verify(password, user["password"]):
        token_data = {
            "sub": str(user["_id"]),
            "username": user["username"],
            "role": user.get("role"),
        }
        token = create_access_token(token_data)
        refresh_token = generate_refresh_token(token_data)
        return JSONResponse(
            {
                "access_token": token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "role": user.get("role"),
                "username": user["username"],
            }
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/logout", response_model=None)
async def logout(
    token: str = Depends(oauth2_scheme), refresh_token: str = Form(...)
) -> JSONResponse:
    try:
        blacklist_token(refresh_token)
        blacklist_token(token)
    except JWTError as e:
        if "Signature has expired" in str(e):
            return JSONResponse(
                status_code=401,
                content={
                    "status": "error",
                    "message": "Token has expired",
                },
            )
        raise
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Logged out successfully",
        },
    )


@token_router.post(
    "/refresh-token",
    response_model=None,
    responses={
        200: {
            "description": "Successful Token Refresh",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "string",
                        "token_type": "string",
                        "role": "string",
                        "username": "string",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {"example": {"detail": "Invalid refresh token"}}
            },
        },
    },
)
async def refresh_token(
    refresh_token: str = Form(...),
    access_token: str = Depends(oauth2_scheme),
) -> JSONResponse:
    """
    Refresh the access token using a refresh token.

    Args:
        refresh_token (str): The refresh token.

    Returns:
        JSONResponse: A JSON response containing the new access token, token type, role, and username.

    Raises:
        HTTPException: If the provided refresh token is invalid.
    """
    try:
        user_id = verify_refresh_token(refresh_token)
        if user_id:
            user_in_company = db.Company.find_one({"_id": ObjectId(user_id)})
            user_in_developers = db.Developers.find_one({"_id": ObjectId(user_id)})

            user = user_in_company or user_in_developers
            if user:
                blacklist_token(access_token)
                token_data = {
                    "sub": str(user["_id"]),
                    "username": user["username"],
                    "role": user.get("role"),
                }
                new_access_token = create_access_token(token_data)
                return JSONResponse(
                    {
                        "access_token": new_access_token,
                        "token_type": "bearer",
                        "role": user.get("role", ""),
                        "username": user["username"],
                    }
                )

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"{e}")


@router.post("/reset-password")
async def reset_password(
    reset_password_input: ResetPasswordInput,
    current_user: dict = Depends(get_current_user),
):
    """
    Reset the user's password.

    Args:
        reset_password_input (ResetPasswordInput): The current and new password.
        current_user (dict): The current user.

    Returns:
        dict: A success message.

    Raises:
        HTTPException: If the current password is incorrect.
    """
    user_id = current_user["sub"]
    user_in_company = db.Company.find_one({"_id": ObjectId(user_id)})
    user_in_developers = db.Developers.find_one({"_id": ObjectId(user_id)})
    user = user_in_company or user_in_developers

    # Verify the current password
    if not pwd_context.verify(reset_password_input.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Hash the new password
    new_password_hashed = pwd_context.hash(reset_password_input.new_password)

    # Update the user's password in the database
    if user_in_company:
        db.Company.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": new_password_hashed}})
    else:
        db.Developers.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": new_password_hashed}})

    return {"message": "Password has been reset successfully"}