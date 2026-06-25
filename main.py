from fastapi import FastAPI,Query,HTTPException
from typing import Annotated
from pydantic import BaseModel,Field
from datetime import datetime
from enum import Enum
class Login(BaseModel):
    username:str|None=None
    email_id:str
    password:str
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
users=[
    {
        "id":1,
        "email":"admin@company.com",
        "username":"admin",
        "password":"admin@123",
        "role":"admin",
        "created_at":datetime.now()
    },
    {
        "id":2,
        "email":"manager@company.com",
        "username":"manager",
        "password":"manager@123",
        "role":"manager",
        "created_at":datetime.now()
    },
    {
        "id":3,
        "email":"user@company.com",
        "username":"user",
        "password":"user@123",
        "role":"user",
        "created_at":datetime.now()
    }
]
projects=[]
#find user : to  be later used in create-project
def find_user(id):
    for i in users:
        if i["id"]==id:
            return(i)
        
#register function
@app.post("/api/v1/auth/register/")
async def register(userReg:UserRegister):
    new_user={
    "id":len(users)+1,
    "email":userReg.email,
    "username":userReg.username,
    "password":userReg.password,
    "role":"user",
    "created_at":datetime.now()
    }
    users.append(new_user)
    return new_user
#login feature
@app.post("/api/v1/auth/login/")
async def login(data:Login,name:Annotated[str|None,Query(max_length=50)]=None):
    user=checkuser(data)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized error ! Email and Password doesnt match"
        )
    else:
        data_dict=data.model_dump()
        if data.email_id=="admin@company.com":
            data_dict.update({"Admin":"Full access: create, read, update, delete any project"})
        elif data.email_id=="manager@company.com":
            data_dict.update({"Manager":"Create,Read,update any project--Cannot delete"})
        else:
            data_dict.update({"User":"Create projects; read/update only own projects"})
        if name:
            data_dict.update({"Name":name})
        return data_dict
    
#reading the users
@app.get("/api/v1/users/")
async def read_users():
    #for accessing a global parameter, dont use query parameter
    return users
#finding role
def find_role(id):
    for i in users:
        if i["id"]==id:
            return i["role"]
#create projects
@app.post("/api/v1/create_projects")
async def create_project(user_id:int,project:Projects):
    owner=find_user(user_id)
    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="User with this ID doesnot exist"
        )
    new_project={
        "id":len(projects)+1,
        "title":project.title,
        "description":project.description,
        "status":"draft",
        "owner_id":owner["id"],
        "owner_username":owner["username"],
        "created_at":datetime.now(),
        "updated_at":datetime.now()
    }
    projects.append(new_project)
    return new_project
#read projects
@app.get("/api/v1/read_projects/{id}")
async def read_projects(id:int):
    now_role=find_role(id)
    if(now_role==None):
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if(now_role=="admin" or now_role=="manager"):
        return projects
    else:
        return [i for i in projects if i["owner_id"]==id]
#getting the projects acc to project id:
def find_project(pid):
    for i in projects:
        if(i["id"]==pid):
            return i
@app.get("/api/v1/projects/{project_id}/{uid}")
async def get_project(project_id:int,uid:int):
    #here we are passing the project id
    project=find_project(project_id)
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    user=find_user(uid)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    role=find_role(uid)
    if(project["owner_id"]==uid or role=="admin" or role=="manager"):
        return project
    else:
        raise HTTPException(
            status_code=403,
            detail="403 Forbidden- Unauthorized access"
        )
#JWT Authentication
def checkuser(data):
    for i in users:
        if((i["email"]==data.email_id) and (i["password"]==data.password)):
                return i
    return None