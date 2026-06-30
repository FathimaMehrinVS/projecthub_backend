#Version 1
from fastapi import FastAPI,Response,HTTPException,Depends
from pydantic import BaseModel,Field
from datetime import datetime,timedelta,timezone
from enum import Enum
from jose import jwt
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from passlib.context import CryptContext
SECRET_KEY="projecthub_backend_fastapi_2026"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
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
class UpdateProject(BaseModel):
    title:str|None=None
    description:None|str=None
    status:Status|None=None
    role:Role
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
projects=[
    {
  "id": 1,
  "title": "Salary Dashboard",
  "description": "Efficient system to showcase salary management",
  "status": "draft",
  "owner_id": 1,
  "owner_username": "admin",
  "created_at": datetime.now(),
  "updated_at": datetime.now()
},
{
  "id": 2,
  "title": "Pet adoption centre",
  "description": "A system to manage pet adoption and care",
  "status": "draft",
  "owner_id": 1,
  "owner_username": "admin",
  "created_at": datetime.now(),
  "updated_at": datetime.now()
},
{
  "id": 3,
  "title": "Flora and Fauna",
  "description": "A library system for reading books related to flora and fauna",
  "status": "draft",
  "owner_id": 2,
  "owner_username": "manager",
  "created_at": datetime.now(),
  "updated_at": datetime.now()
},
{
  "id": 4,
  "title": "Library Management system",
  "description": "A management system for a library.",
  "status": "draft",
  "owner_id": 2,
  "owner_username": "manager",
  "created_at": datetime.now(),
  "updated_at": datetime.now()
},
{
  "id": 5,
  "title": "Classroom Management system",
  "description": "A management system for a classroom.",
  "status": "draft",
  "owner_id": 3,
  "owner_username": "user",
  "created_at": datetime.now(),
  "updated_at": datetime.now()
}
]
#create token function:
def create_access_token(data):
    to_encode=data.copy()
    expiry=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expiry})
    return jwt.encode(
        to_encode,
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
#check duplicate email id used:
def check_existing_user(email):
    for i in users:
        if i["email"]==email:
            raise HTTPException(
                status_code=400,
                detail="Email is already in use"
            )
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
    user_id=int(payload["sub"])
    user_record=find_user(user_id)
    if(user_record is None):
        raise HTTPException(
            status_code=401,
            detail="User not found!"
        )
    return user_record       
#register function
@app.post("/api/v1/auth/register",status_code=201)
async def register(userReg:UserRegister):
    new_user={
    "id":len(users)+1,
    "email":userReg.email,
    "username":userReg.username,
    "password":hash_password(userReg.password),
    "role":Role.user.value,
    "created_at":datetime.now()
    }
    check_existing_user(new_user["email"])
    users.append(new_user)
    return {
    "id":new_user["id"],
    "email":new_user["email"],
    "username":new_user["username"],
    "role":new_user["role"],
    "created_at":new_user["created_at"]
    }
#login feature
@app.post("/api/v1/auth/login",status_code=200)
async def login(form_data:OAuth2PasswordRequestForm=Depends()):
    user=checkuser(form_data)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials ! Email and Password doesnt match"
        )
    payload = {
        "sub" : str(user["id"]),
        "role":user["role"],
    }
    token=create_access_token(payload)
    return {
        "access_token":token,
        "token_type":"bearer"
    }
#reading the users
@app.get("/api/v1/users")
async def read_users():
    #for accessing a global parameter, dont use query parameter
    return [
        {
        "id":i["id"],
        "email":i["email"],
        "username":i["username"],
        "role":i["role"],
        "created_at":i["created_at"]
        }
        for i in users
    ]
#create projects
@app.post("/api/v1/projects",status_code=201)
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
@app.get("/api/v1/projects",status_code=200)
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
    return None
@app.get("/api/v1/projects/{project_id}",status_code=200)
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
@app.get("/api/v1/auth/me",status_code=200)
async def current_user(user_record=Depends(get_current_user)):
    return {
        "id":user_record["id"],
        "email":user_record["email"],
        "username":user_record["username"],
        "role":user_record["role"],
        "created_at":user_record["created_at"]
    }
#Update a specific project:
@app.put("/api/v1/projects/{project_id}",status_code=200)
#Update a project's title, description, or status.
async def update_project(project_id:int,upd_proj:UpdateProject,user=Depends(get_current_user)):
    p=find_project(project_id)
    if p is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    uid=p["owner_id"]
    allowed={
    "draft":["active","draft"],
    "active":["completed",'archived',"active"],
    "completed":["archived","completed"],
    "archived":['archived']
    }
    if(user["role"]=='admin' or user["role"]=='manager' or user["id"]==uid):
        #find the project based on pid:
        if upd_proj.title is not None:
            p["title"]=upd_proj.title
        if upd_proj.description is not None:
            p["description"]=upd_proj.description
        if upd_proj.status is not None:
            current=p["status"]
            new=upd_proj.status.value
            if new not in allowed[current]:
                raise HTTPException(
                    status_code=400,
                    detail="Bad Request ! Invalid Status transition"
                )
            p["status"]=new
    else:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized request"
        )
    p["updated_at"]=datetime.now()
    #valid status transitions:
    return p
#Delete projects
@app.delete("/api/v1/projects/{project_id}",status_code=204)
async def del_proj(project_id:int,user=Depends(get_current_user)):
    p=find_project(project_id)
    if p is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )
    if user['role']=="admin":
        projects.remove(p)
    else:
        raise HTTPException(
            status_code=403,
            detail="Forbidden request ! Only admin can delete a project"
        )
    return {
        "message":"Project deleted successfully"
    }