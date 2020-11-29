from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    email: str


@app.get("/items/{item_id}")
def read_root(item_id: str, request: Request):
    client_host = request.client.host
    return {"client_host": client_host, "item_id": item_id}


@app.post("/items/{item_id}")
def add_item(item_id: str, user: User, request: Request):
    client_host = request.client.host
    return {"item_id": item_id, "client_host": client_host, "username": user.username, "email": user.email}