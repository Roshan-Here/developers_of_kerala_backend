from fastapi import APIRouter, Security
from app.api.api_v1.endpoints import company, developer, job, user, waitlist, contact,blog
from app.api.deps import get_current_user

api_router = APIRouter()


api_router.include_router(user.router, prefix="/user", tags=["User"])
api_router.include_router(user.token_router, prefix="/user", tags=["User"])
api_router.include_router(
    company.router,
    prefix="/company",
    tags=["company"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    developer.router,
    prefix="/developers",
    tags=["developers"],
    dependencies=[Security(get_current_user)],
)
api_router.include_router(
    job.router, prefix="/job", tags=["job"], dependencies=[Security(get_current_user)]
)
api_router.include_router(waitlist.router, prefix="/waitlist", tags=["waitlist"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
# blog router
api_router.include_router(
    blog.router,
    prefix="/blog",
    tags=["blog"],
    dependencies=[Security(get_current_user)],
) 