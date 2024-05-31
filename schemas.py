from pydantic import BaseModel
from typing import List, Optional, Union

class BaseBlog(BaseModel):
    title: str
    body: str

class Blog(BaseBlog):
    class Config():
        orm_mode = True
        
class User(BaseModel):
    name: str
    email: str
    password: str        

class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[Blog] = [] 
    class Config():
        orm_mode = True

class ShowBlog(BaseModel):
    # since we dont need id we are not adding it
    title: str
    body: str
    creator: ShowUser
    class Config():
        orm_mode = True

class Login(BaseModel):
    username: str
    password: str        

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Union[str, None] = None
    scopes: List[str] = []
