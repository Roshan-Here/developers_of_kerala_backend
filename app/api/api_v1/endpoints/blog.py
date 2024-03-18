"""
things to do:
first 
    create blog Model,
        - Title : str
        - Author - get_current_user()
        - Content : str
        - images : list[str], can't be None save as str
"""
import os
import shutil
from fastapi import APIRouter,Form,File,UploadFile,Depends,HTTPException
from fastapi.responses import JSONResponse
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.upload import digital_ocean_upload
from app.db.engine import db
from app.schemas.blog import retrive_blog,BlogModel

router = APIRouter()

# create blog
@router.post(
    "/create",
    response_description="Create new Blog",
    responses={
        400:{'description':'Bad Request'},
        401:{'description':'Unauthorized'},
        500:{'description':'Internal Server Error'},
        201:{'description':'Sucessfull Responce'},
    }
)
async def create_blog(
    Title : str = Form(...,description="Title of the blog"),
    Content : str = Form(...,description="Content of the blog"),
    Author : dict = Depends(get_current_user),
    images : list[UploadFile] = File(None,description="List of images for the blog"),
):
    Author = Author["username"]
    image_array = []
    if images:
        for image in images:
            file_name = str(image.filename) 
            if file_name.lower().endswith(tuple(settings.ALLOWED_IMAGE_FORMATS)):
                content = await image.read()
                location = os.path.join(settings.MEDIA_URI,f"{Author}")
                try:
                    req_path = f"{Author}/{Title}/{file_name}"
                    os.makedirs(location,exist_ok=True)
                    org_location = os.path.join(location,f"{Title}")
                    os.makedirs(org_location,exist_ok=True)
                    upload_location = os.path.join(org_location,f"{file_name}")
                    with open(upload_location,"wb") as f:
                        f.write(content)
                        # image_array.append(upload_location)
                    digital_ocean_upload(upload_location=upload_location,custom_path=req_path)
                    download_path = f"{settings.endpoint_url}/{settings.bucket_name}/{req_path}"
                    image_array.append(download_path)
                except Exception as e:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message":str(e),
                        }
                    )
                # remove stored local Files
                shutil.rmtree(location)
            else:
                print(f"not required file type {image.filename}")
                pass
    print(image_array)
    blog_dict = {
        "Title" : Title,
        "Content" : Content,
        "Author" : Author,
        "images" : image_array
    }
    blog = db.Blog.insert_one(blog_dict)
    new_blog = db.Blog.find_one({"_id":blog.inserted_id})
    return retrive_blog(new_blog)
    

"""     
#second
    setup endpoint for create,
        setup digital ocean credentials
        get media_upload_dir from core/config . MEDIA_DIR
            setup MEDIA_DIR as Author/Title/images
        check if Title exist in db, for current_user -> e
        then put images in Digital Ocean
        put datas into db.blogs   
"""


@router.get(
    "/",
    response_description="Get all Blog Datas",
    response_model=BlogModel,
    responses={
        404: {"description": "No Blog found"},
        401: {"description": "Unauthorized"},
        200: {"description": "Successful Response"},
    },
)
async def retrive_all_blog():
    try:
        all_blog = db.Blog.find()
        datas = []
        for x in all_blog:
            datas.append(retrive_blog(x))
        return JSONResponse(
            status_code=200,
            content={
                "status":"success",
                   "data": datas,
            }
        ) 
    except Exception as e:
        return HTTPException(
            status_code=500,
            detail={
                "status":"error",
                "message":str(e),
            }
        )