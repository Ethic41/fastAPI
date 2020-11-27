import time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, Path, Query, Body, Cookie, Header, File, UploadFile, Form, HTTPException, Request, status

app = FastAPI()


class Item(BaseModel):
    name: str
    description: Optional[str] = Field(None, title="The description of the item", max_length=300)
    price: float = Field(..., gt=0, description="the price must be greater than zero")
    tax: Optional[float] = None
    level: int


class ItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str] = Field(None, title="The description of the item", max_length=300)
    price: float = Field(..., gt=0, description="the price must be greater than zero")
    tax: Optional[float] = None
    level: Optional[int] = 3


class ModelName(str, Enum):
    alexnet = "alexnet"
    lenet = "lenet"
    resnet = "resnet"


class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class UserIn(BaseModel):
    username: str
    password: str
    email: EmailStr
    full_name: Optional[str] = None


class UserOut(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserOld(BaseModel):
    username: str
    full_name: Optional[str] = None


items_db = {
    "foo": {"name": "Mr. Foo", "price": 50.2, "level": 1},
    "bar": {"name": "Mr. Bar", "price": 25.4, "level": 2}
}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False
    },

    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True
    }

}


def fake_hashed_password(password: str):
    return f"fakehashed{password}"


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
            status_code=400, detail="Inactive User"
        )

    return current_user


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = UserInDB(**user_dict)
    hashed_password = fake_hashed_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/authitems/")
async def read_items(token: str = Depends(oauth2_scheme)):
    return {"token": token}


@app.patch("/items_update/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemUpdate):
    stored_item_data = items_db[item_id]
    stored_item_model = Item(**stored_item_data)
    update_data = item.dict(exclude_unset=True)
    updated_item = stored_item_model.copy(update=update_data)
    items_db[item_id] = jsonable_encoder(updated_item)
    return updated_item


@app.get("/item_with_error/{item_id}")
async def item_with_error(item_id: str):
    db_items = {"foo": "there is foo", "bar": "there bar"}
    if item_id not in db_items:
        raise HTTPException(status_code=404, detail=f"there is no item {item_id}")

    return {"item": db_items[item_id]}


@app.post("/formfile/")
async def multi_files(filea: bytes = File(...), fileb: UploadFile = File(...), token: str = Form(...)):
    return {
        "file_a_size": len(filea),
        "file_b_type": fileb.content_type,
        "token": token
    }


@app.post("/files/")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    return {"filename": file.filename, "file_type": file.content_type}


@app.post("/user/", response_model=UserOut)
async def create_user(user: UserIn):
    return user


@app.get("/itemscookie/")
async def read_itemsc(cookie_id: Optional[str] = Cookie(None), user_agent: Optional[str] = Header(None)):
    return {"cookie_id": cookie_id, "User-Agent": user_agent}


@app.put("/items/{item_id}")
async def update_itema(item_id: int, item: Item = Body(..., embed=True)):
    results = {"item_id": item_id, "item": item}
    return results


@app.get("/")
async def root():
    return {"message": "Hello, World!"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


""" @app.get("/users/current_user")
async def get_current_user():
    return {"user": "System User"}
 """

@app.get("/users/{user_id}")
async def get_user_old(user_id: int):
    return {"user": user_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "some residual stuff"}


fake_db_items = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


""" @app.get("/dbitems/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_db_items[skip: skip + limit] """


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: str, q: Optional[str] = None, short: bool = False):
    item = {"item_id": item_id, "owner_id": user_id}

    if q:
        item.update({"q": q})

    if not short:
        item.update({"description": "This is an amazing long text that has long description"})
    return item


@app.get("/reqitem/{item_id}")
async def read_req_item(item_id: str, needy: str):
    item = {"item_id": item_id, "needy": needy}
    return item


@app.get("/itemsa/")
async def read_itemsa(q: Optional[str] = Query(None, min_length=3, max_length=5)):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/itemsb/{item_id}")
async def read_itemsb(q: str, item_id: int = Path(..., title="The ID of the item to get")):
    results = {"item_id": item_id}

    if q:
        results.update({"q": q})
    return results

# @app.put("/items/{item_id}")
# async def update_item(item_id: int, item: Item, user: User, importance: int = Body(...)):
# return {"item_id": item_id, "item": item, "user": user, "importance": importance}
