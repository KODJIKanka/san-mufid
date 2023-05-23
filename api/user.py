from fastapi import FastAPI, HTTPException
from models import User, User_Pydantic, UserIn_Pydantic
from tortoise.contrib.fastapi import HTTPNotFoundError, register_tortoise
from pydantic import BaseModel

class Message(BaseModel):
    message : str


app = FastAPI()

# Insertion d'utilisateur dans la base de données

@app.post("/user", response_model= User_Pydantic)
async def create_user(user:UserIn_Pydantic):
    obj = await User.create(**user.dict(exclude_unset=True ))
    return await User_Pydantic.from_tortoise_orm(obj)

# Récupération d'un utilisateur  depuis la base de données

@app.get("/user/{id}", response_model=UserIn_Pydantic, responses={404:{"model":HTTPNotFoundError}})
async def get_one(id:int):
    return await UserIn_Pydantic.from_queryset_single(User.get(id=id))

# Suppréssion d'un utilisateur de la base  de données

@app.delete("/user/{id}", response_model=Message, responses={404:{"model":HTTPNotFoundError}})
async def delete_user(id:int):
    del_obj=await User.filter(id=id)
    if not del_obj:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return Message(message="Suppression réussie")


# Création et configuration de la base de données SQLite

register_tortoise(
    app,
    db_url="sqlite://store.db",
    modules={'models':['models']},
    generate_schemas = True,
    add_exception_handlers = True

)