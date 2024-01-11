from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pymongo.errors import ServerSelectionTimeoutError
from passlib.context import CryptContext
from bson.objectid import ObjectId
from typing import List, Optional

from fastapi import Depends, HTTPException

from typing import Optional
from dotenv import load_dotenv
from models import DeveloperProfileUpdate, CompanyProfileUpdate,Opening,OpeningStatus

from database import db
from models import UserRegistration, Opening, OpeningStatus
from authentication import create_access_token, get_current_user

# Load environment variables from .env file
load_dotenv()
# FastAPI intialization
app = FastAPI()
# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return "<h1>Hello Kerala Developers!</h1>"


@app.get("/check_db")
async def check_db_connection():
    try:
        # The ismaster command is cheap and does not require auth.
        db.command("ismaster")
        return {"status": "Database is connected"}
    except ServerSelectionTimeoutError as e:
        return {"status": "Database connection failed", "exception": str(e)}


@app.post("/submit_email/")
async def submit_email(email: str = Form(...)):
    print(f"Received email: {email}")
    try:
        result = db.waitlist.insert_one({"email": email})
        if result.inserted_id:
            return {
                "message": "Email inserted successfully",
                "email_id": str(result.inserted_id),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to insert")
    except Exception as e:
        return {"exception": str(e)}


@app.post("/create_developer/")
async def create_developer(
    name: str, place: str, skills: str, email: str, resume: Optional[str] = None
):
    try:
        # Create a dictionary for developer data
        developer_data = {
            "name": name,
            "place": place,
            "skills": skills,
            "email": email,
            "resume": resume,
        }

        # Insert the developer data into the collection
        result = db.developers_talent.insert_one(developer_data)

        if result.inserted_id:
            return {
                "message": "Developer created successfully",
                "developer_id": str(result.inserted_id),
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create developer")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create developer: {str(e)}"
        )


@app.get("/list_developers/")
async def list_developers():
    # try:
    # Fetch all developers from the collection
    developers = db.developers_talent.find()

    # Convert MongoDB cursor
    # list of dictionaries with ObjectId converted to string
    developers_list = [
        {**developer, "_id": str(developer["_id"])} for developer in developers
    ]

    # Return the list of developers
    return developers_list


@app.post("/register")
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
):
    """
    Register a new user.

    Args:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password of the user.
        role (str): The role of the user.

    Returns:
        dict: A dictionary containing the message and user_id if the user is registered successfully.

    Raises:
        HTTPException: If failed to register the user.
    """
    user_dict = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    }
    user_dict["password"] = pwd_context.hash(user_dict["password"])
    result = db.UserRegistration.insert_one(user_dict)
    if result.acknowledged:
        return JSONResponse(
            status_code=200,
            content={
                "message": "User registered successfully",
                "user_id": str(result.inserted_id),
            },
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to register user")


@app.post("/login")
async def generate_token(username_or_email: str = Form(...), password: str = Form(...)):
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
    user = db.UserRegistration.find_one(
        {"$or": [{"username": username_or_email}, {"email": username_or_email}]}
    )
    if user and pwd_context.verify(password, user["password"]):
        token_data = {
            "sub": str(user["_id"]),
            "username": user["username"],
            "role": user.get("role", ""),
        }
        token = create_access_token(token_data)
        return JSONResponse(
            {
                "access_token": token,
                "token_type": "bearer",
                "role": user.get("role", ""),
                "username": user["username"],
            }
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
async def logout():
    """
    Log out a user.
    Invalidate the user's access token.

    Returns:
        JSONResponse: A JSON response indicating that the user has been logged out.

    Note for front-end developers:
        When this endpoint is called, the client should delete the access token from local storage.
        This will simulate a logout operation by preventing the client from making authenticated requests to the server.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Logged out successfully",
        },
    )


@app.post("/update_company_profile", status_code=200)
async def company_profile_update(
    profile: CompanyProfileUpdate, current_user: dict = Depends(get_current_user)
):
    """
    Update the company profile with the provided data.

    Parameters:
    - profile: CompanyProfileUpdate - The data to update the company profile.
    - current_user: dict - The current user's information.

    Returns:
    - dict: A dictionary containing the message and updated user data if successful, or an error message if something goes wrong.
    """
    if current_user.get("role") != "company":
        raise HTTPException(
            status_code=403, detail="Access denied. Role must be company."
        )
    else:
        try:
            user_data = profile.dict(exclude_unset=True)

            # Update the user data in the UserRegistration collection
            result = db.UserRegistration.update_one(
                {"_id": ObjectId(current_user["sub"])}, {"$set": user_data}
            )

            if result.modified_count > 0:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "Company Profile Updated Successfully",
                        "data": user_data,
                    },
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "success",
                        "message": "No changes made to the Company Profile",
                        "data": user_data,
                    },
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": str(e),
                    "data": None,
                },
            )


@app.get("/company_profile/{company_id}")
async def view_company_profile(company_id: str):
    """
    Retrieve the profile of a company by its ID.

    Args:
        company_id (str): The ID of the company.

    Returns:
        dict: A dictionary containing the company profile if found, or a message if not found.
    """

    try:
        # Find the company by its ID
        company = db.UserRegistration.find_one(
            {"_id": ObjectId(company_id)}, {"password": 0}
        )
        if company:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "data": {**company, "_id": str(company["_id"])},
                },
            )
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": "Company not found",
                },
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
            },
        )


@app.get("/company_list")
async def retrieve_company_list():
    """
    Retrieve the list of companies from the collection.

    Returns:
        dict: A dictionary containing the list of companies.
            Each company is represented as a dictionary with the "_id" field converted to a string.
    """
    try:
        # Fetch all companies from the collection
        companies = db.UserRegistration.find({"role": "company"}, {"password": 0})
        company_list = [
            {**company, "_id": str(company["_id"])} for company in companies
        ]
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": company_list,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
            },
        )


@app.post("/insert_job", response_model=Opening)
async def insert_job(
    job_role: str,
    skills_needed : List[str],
    qualification_required: str,
    job_description: str,
    no_of_openings: int = 1,
    status: str = "active"
):
    """
    Insert a new job opening into the MongoDB collection.

    Args:
        opening (Opening): Details of the job opening.

    Returns:
        Opening: Details of the inserted job opening.
    """
    try:
        opening = Opening(
            job_role=job_role,
            skills_needed=skills_needed,
            qualification_required=qualification_required,
            job_description=job_description,
            no_of_openings=no_of_openings,
            status=status
        )
        # Insert the job opening into the MongoDB collection
        result = db.openings.insert_one(opening.dict())

        # Get the inserted document's ID
        inserted_id = result.inserted_id

        return JSONResponse(
            status_code=201,
            content={
                "status": "success",
                "inserted_id": str(inserted_id)
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
            },
        )

# needs atlease one paramter in search
def at_least_one_required(
    skills_needed: str = None,
    qualification_required: str = None,
    job_role: str = None,
    job_description: str = None,
):
    print('skills needed:',skills_needed)
    # Check if at least one field is provided
    if not any([skills_needed, qualification_required, job_role, job_description]):
        raise HTTPException(status_code=422, detail="At least one field is required")
    
     # Ensure skills_needed is not an empty list
    if skills_needed is not None and not skills_needed:
        raise HTTPException(status_code=422, detail="Skills_needed should not be an empty list")

    # Return the provided values
    return skills_needed, qualification_required, job_role, job_description



@app.get("/job_search", response_model=List[Opening])
# using Depends to check if atleast one parameter is present
async def job_search(
    params: tuple = Depends(at_least_one_required)
):
    """
    Search for job openings based on specified criteria.

    Args:
        skills_needed (List[str]): List of required skills.
        qualification_required (str): Required qualification.
        job_role (str): Desired job role.
        status (OpeningStatus): Status of the job openings (default is 'active').

    Returns:
        List[Opening]: List of job openings matching the specified criteria.
    """
    # Unpack the tuple
    skills_needed, qualification_required, job_role, job_description = params
    print('skills needed:',skills_needed)
    if skills_needed:
        skills_needed = skills_needed.split(",")
    try:
        # MongoDB query to fetch job openings
        query = {
            # "skills_needed": skills_needed,
            # "skills_needed": {"$in": skills_needed} if skills_needed else None,
            "qualification_required": qualification_required,
            "job_role": job_role,
            "job_description": job_description,
            # "status": "active",
        }

        print("query",query)
        job_openings_list = []
        # Fetch job openings from the database based on the provided criteria
        for opening in db.openings.find():
            print(opening)
            job_openings_list.append(opening)
        return job_openings_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
            },
        )
