from fastapi import APIRouter, Form, HTTPException, Depends
from app.db.engine import db
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/submit/{email}")
async def submit_waitlist_email(email: str):
    print(f"Received waitlist email: {email}")
    try:
        result = db.waitlist.insert_one({"email": email})
        if result.inserted_id:
            return {
                "message": "Waitlist email submitted successfully",
                "email_id": str(result.inserted_id),
            }
        else:
            raise HTTPException(
                status_code=500, detail="Waitlist email submission failed"
            )
    except Exception as e:
        return {"error": str(e)}


@router.get("/list")
async def list_waitlist_emails(current_user: dict = Depends(get_current_user)):
    try:
        waitlist_emails = list(db.waitlist.find({}, {"_id": 0, "email": 1}))
        return {"waitlist_emails": waitlist_emails}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing waitlist emails: {str(e)}"
        )
