from fastapi import FastAPI,Query,HTTPException,Depends
from pydantic import BaseModel,Field
from datetime import datetime
from enum import Enum
from jose import jwt
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from passlib.context import CryptContext
SECRET_KEY="projecthub_backend_fastapi_2026"
ALGORITHM="HS256"
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/")
pwd_context=CryptContext(
schemes=["bcrypt"],
deprecated="auto"
)
class Projects(BaseModel):
    title:str=Field(min_length=1)
    description:str|None=None
class Status(Enum):
    draft="draft"
    active="active"
    completed="completed"
    archived="archived"
class Role(Enum):
    user="user"
    admin="admin"
    manager="manager"
class Users(BaseModel):
    id:int
    email:str
    username:str
    password:str
    role:Role
    created_at:datetime
class UserRegister(BaseModel):
    email:str
    username:str
    password:str
app=FastAPI()
#Passlib helper functions
def hash_password(pwd):
    return pwd_context.hash(pwd)
def verify_password(pwd,hash):
    return pwd_context.verify(pwd,hash)
users=[
    {
        "id":1,
        "email":"admin@company.com",
        "username":"admin",
        "password":hash_password("admin@123"),
        "role":"admin",
        "created_at":datetime.now()
    },
    {
        "id":2,
        "email":"manager@company.com",
        "username":"manager",
        "password":hash_password("manager@123"),
        "role":"manager",
        "created_at":datetime.now()
    },
    {
        "id":3,
        "email":"user@company.com",
        "username":"user",
        "password":hash_password("user@123"),
        "role":"user",
        "created_at":datetime.now()
    }
]
projects=[]
#create token function:
def create_access_token(data):
    return jwt.encode(
        data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
#decoding token (verifying token)
def verify_token(token):
    payload=jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )
    return payload
def checkuser(data):
    for i in users:
        if((i["email"]==data.username) and verify_password(data.password,i["password"])):
                return i
    return None
#find user : to  be later used in create-project
def find_user(id):
    for i in users:
        if i["id"]==id:
            return(i)
def get_current_user(token=Depends(oauth2_scheme)):
    try:
        payload=verify_token(token)
    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    user_id=payload["user_id"]
    user_record=find_user(user_id)
    if(user_record is None):
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )
    return user_record       
#register function
@app.post("/api/v1/auth/register/")
async def register(userReg:UserRegister):
    new_user={
    "id":len(users)+1,
    "email":userReg.email,
    "username":userReg.username,
    "password":hash_password(userReg.password),
    "role":"user",
    "created_at":datetime.now()
    }
    users.append(new_user)
    return new_user
#login feature
@app.post("/api/v1/auth/login/")
async def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user=checkuser(form_data)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized error ! Email and Password doesnt match"
        )
    payload = {
        "user_id" : user["id"],
        "email" : user["email"],
        "role":user["role"]
    }
    token=create_access_token(payload)
    return {
        "access_token":token,
        "token_type":"bearer"
    }
#reading the users
@app.get("/api/v1/users/")
async def read_users():
    #for accessing a global parameter, dont use query parameter
    return users
#create projects
@app.post("/api/v1/create_projects")
async def create_project(project:Projects,user=Depends(get_current_user)):
    new_project={
        "id":len(projects)+1,
        "title":project.title,
        "description":project.description,
        "status":"draft",
        "owner_id":user["id"],
        "owner_username":user["username"],
        "created_at":datetime.now(),
        "updated_at":datetime.now()
    }
    projects.append(new_project)
    return new_project
#read projects
@app.get("/api/v1/read_projects")
async def read_projects(user=Depends(get_current_user)):
    id=user["id"]
    now_role=user["role"]
    if(now_role=="admin" or now_role=="manager"):
        return projects
    else:
        return [i for i in projects if i["owner_id"]==id]
#getting the projects acc to project id:
def find_project(pid):
    for i in projects:
        if(i["id"]==pid):
            return i
@app.get("/api/v1/projects/{project_id}")
async def get_project(project_id:int,user=Depends(get_current_user)):
    #here we are passing the project id
    uid=user["id"]
    project=find_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    role=user["role"]
    if(project["owner_id"]==uid or role=="admin" or role=="manager"):
        return project
    else:
        raise HTTPException(
            status_code=403,
            detail="403 Forbidden- Unauthorized access"
        )
#JWT Authentication
@app.get("/api/v1/auth/me")
async def current_user(user_record=Depends(get_current_user)):
    return user_record 