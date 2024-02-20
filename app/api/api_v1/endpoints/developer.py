"""
developers.py

This module contains the routes for handling operations related to developers.
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from app.schemas.developer import DeveloperProfile, UpdateDeveloperModel
from app.db.engine import db
from fastapi import Query
from bson import ObjectId
from pymongo import ReturnDocument

router = APIRouter()


@router.get(
    "/",
    response_description="List all developers",
    response_model=UpdateDeveloperModel,
    response_model_by_alias=False,
    responses={
        404: {"description": "No developers found"},
        401: {"description": "Unauthorized"},
        200: {"description": "Successful Response"},
    },
)
async def retrieve_developer_list():
    """
    Retrieve the list of developers from the collection.

    Returns:
    - dict: A dictionary containing the list of developers.

    Raises:
    - HTTPException: If there is an error while retrieving the developer list.
    """
    try:
        # Fetch all developers from the collection
        developers = db.Developers.find({"role": "developer"}, {"password": 0})
        developer_list = [
            {**developer, "_id": str(developer["_id"])} for developer in developers
        ]
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": developer_list,
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


@router.get(
    "/search",
    response_description="Search for developers based on criteria",
    response_model=list[DeveloperProfile],
    response_model_by_alias=False,
    responses={
        404: {"description": "No developers found"},
        401: {"description": "Unauthorized"},
        200: {"description": "Successful Response"},
    },
)
async def search_developers(
    field: str = Query(..., description="The field to search by"),
    value: str = Query(..., description="The value to search for"),
):
    """
    Search for companies based on a specific field and value.

    Parameters:
    - field (str): The field to search by (e.g., "company_name", "industry", etc.).
    - value (str): The value to search for in the specified field.

    Returns:
    - List[CompanyProfile]: A list of companies matching the search criteria.

    Raises:
    - HTTPException: If there is an error during the search or no companies are found.
    """
    try:
        # Create a dynamic query to find companies based on the provided field and value
        search_query = {"role": "developer", field: {"$regex": value, "$options": "i"}}
        print("search_query:", search_query)
        developers = db.Developers.find(search_query, {"password": 0})
        # Convert ObjectId to string for each company in the result
        developer_list = [
            {**developer, "_id": str(developer["_id"])} for developer in developers
        ]

        print("developer_list", developer_list)
        if not developer_list:
            raise HTTPException(status_code=404, detail=f"No developers found")

        return developer_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
            },
        )


@router.post(
    "/post",
    response_description="Create a new developer profile",
    response_model=DeveloperProfile,
    response_model_by_alias=False,
    responses={
        400: {"description": "Bad Request"},
        201: {"description": "Developer profile created successfully"},
        500: {"description": "Internal Server Error"},
    },
)
async def create_developer(developer: UpdateDeveloperModel):
    """
    Create a new developer profile.

    Parameters:
    - developer (DeveloperCreate): The data for creating a new developer profile.

    Returns:
    - DeveloperProfile: The newly created developer profile.

    Raises:
    - HTTPException: If there is an issue creating the developer profile.
    """
    try:
        # Assuming db is your MongoDB connection object
        # and Developers is your MongoDB collection for developers
        result = db.Developers.insert_one(developer.dict(by_alias=True))
        created_developer = db.Developers.find_one({"_id": result.inserted_id})

        if created_developer:
            created_developer["_id"] = str(
                created_developer["_id"]
            )  # Convert ObjectId to string
            return created_developer

        raise HTTPException(
            status_code=500, detail="Failed to create developer profile"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create developer profile: {str(e)}"
        )


@router.get(
    "/{id}",
    response_description="Get a single Developer Profile",
    response_model=DeveloperProfile,
    response_model_by_alias=False,
    responses={
        404: {"description": "Developer not found"},
        401: {"description": "Unauthorized"},
        200: {"description": "Successful Response"},
    },
)
async def get_developer(id: str):
    """
    Get the record for a specific developer, looked up by `id`.

    Parameters:
    - id (str): The ID of the developer to retrieve.

    Returns:
    - dict: The developer profile.

    Raises:
    - HTTPException: If the developer with the specified ID is not found.
    """
    try:
        object_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Invalid ObjectId: {id}")

    if (developer := db.Developers.find_one({"_id": object_id})) is not None:
        developer["_id"] = str(developer["_id"])  # Convert ObjectId to string
        return developer

    raise HTTPException(status_code=404, detail=f"Developer {id} not found")


@router.put(
    "/{id}",
    response_description="Update Developer Profile",
    response_model=DeveloperProfile,
    response_model_by_alias=False,
)
async def update_developer(id: str, developer: UpdateDeveloperModel = Body(...)):
    """
    Update individual fields of an existing developer profile.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.

    Parameters:
    - id (str): The ID of the developer profile to be updated.
    - developer (UpdateDeveloperModel): The updated developer profile data.

    Returns:
    - DeveloperProfile: The updated developer profile.

    Raises:
    - HTTPException: If the developer profile with the given ID is not found.
    """
    developer_dict = developer.dict(by_alias=True)
    developer_updates = {k: v for k, v in developer_dict.items() if v is not None}
    if developer_updates:
        updated_developer = db.Developers.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": developer_updates},
            return_document=ReturnDocument.AFTER,
            upsert=True,
        )

        if updated_developer:
            updated_developer["_id"] = str(
                updated_developer["_id"]
            )  # Convert ObjectId to string
            return updated_developer

    # The update is empty, but we should still return the matching document:
    if (developer := db.Developers.find_one({"_id": ObjectId(id)})) is not None:
        developer["_id"] = str(developer["_id"])  # Convert ObjectId to string
        return developer

    raise HTTPException(status_code=404, detail=f"Developer {id} not found")


# @router.delete(
#     "/delete",
#     response_description="Delete a  developer",
#     # response_model=Opening,
#     response_model_by_alias=False,
#     responses={
#         401: {"description": "Unauthorized"},
#         200: {"description": "Job posting deleted successfully"},
#     },
# )
# async def delete_developer(developer_id: str):
#     try:
#         # Assuming db is your MongoDB connection object
#         # and Opening is your MongoDB collection
#         try:
#             developer_object_id = ObjectId(developer_id)
#         except Exception:
#             raise HTTPException(status_code=404, detail=f"Invalid ObjectId: {id}")
#         deleted_developer = db.Developers.find_one_and_delete({"_id": developer_object_id})
#         if deleted_developer:
#             deleted_developer["_id"] = str(deleted_developer["_id"])
#             return {"message": "Developer account deleted successfully", "job": deleted_developer}
#         else:
#             raise HTTPException(status_code=404, detail="Job not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")
