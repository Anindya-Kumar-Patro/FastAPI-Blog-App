from fastapi import FastAPI, Depends, status, Response, HTTPException
import schemas, models, database, JWT_token
from sqlalchemy.orm import Session
from typing import List, Union, Annotated
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
app = FastAPI()

models.Base.metadata.create_all(bind=database.engine)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={"me": "Read information about the current user.", "items": "Read items."},
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()    

def get_current_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    return JWT_token.verify_token(token, credentials_exception)

# Pass a response model i.e. what output should be returned after completion
# of the request, can be done by passing response_model = model in param of generator
# tags = under which tag we want our requests to be in localhost:8000/docs
@app.post('/blog', status_code=status.HTTP_201_CREATED, tags=['blog'])
def create(request: schemas.Blog, db:Session = Depends(get_db)):
    new_blog = models.Blog(title=request.title, body=request.body, user_id=1)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@app.delete('/blog/{id}', status_code=status.HTTP_204_NO_CONTENT, tags=['blog'])
def delete_a_blog(id, db:Session = Depends(get_db)):
    ''' This is a function to delete a specific blog from database'''
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Blog with id {id} is not present')
    blog.delete(synchronize_session=False)
    db.commit()
    return {'data': 'Blog is successfully deleted'}

@app.put('/blog/{id}', status_code=status.HTTP_202_ACCEPTED, tags=['blog'])
def update_blog_by_id(id, request:schemas.Blog, db:Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='the blog with this id is not present')
    blog.update(request)    
    db.commit()
    return {'data': 'Blog is updated successfully'}

@app.get('/blog',  response_model=List[schemas.ShowBlog], tags=['blog'])
def get_all_blogs(db:Session = Depends(get_db), get_current_user: schemas.User = Depends(get_current_user)):
    ''' This is a function to get all blogs from database '''
    blogs = db.query(models.Blog).all()
    return blogs

@app.get('/blog/{id}',  response_model=schemas.ShowBlog, tags=['blog'])
def get_blog_by_id(id, response:Response, db:Session = Depends(get_db)):
    ''' Get specific blog using the id parameter '''
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=404, detail=f'Unable to find blog with id: {id}')
    return blog 
    ## This above line is alternative to ones below    
    # response.status_code = status.HTTP_404_NOT_FOUND
    # return {'detail': f'Blog with id: {id} not found'}

# for hashing the pwd
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def pwd_hasher(pwd):
    return pwd_ctx.hash(pwd)

def pwd_checker(hashed_pwd, input_pwd):
    return pwd_ctx.verify(input_pwd, hashed_pwd)

@app.post('/user', status_code = status.HTTP_201_CREATED, response_model=schemas.ShowUser, tags=['user'])
def create_user(request: schemas.User, db:Session = Depends(get_db)):
    new_user = models.User(name=request.name, email=request.email, password=pwd_hasher(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get('/user/{id}', response_model=schemas.ShowUser, tags=['user'])
def get_user_by_id(id:int, db:Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with {id} not found')
    return user  

@app.post('/login', tags=["Authentication"])
def login(request: OAuth2PasswordRequestForm = Depends(), db:Session=Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
        raise HTTPException(detail=f'User with {request.username} is not avaliable', status_code=status.HTTP_404_NOT_FOUND)    
    if not pwd_checker(user.password, request.password):
        raise HTTPException(detail=f'Incorrect Password', status_code=status.HTTP_404_NOT_FOUND)    
    # generate JWT token if credentials are correct
    access_token = JWT_token.create_access_token(data={"sub": user.email})
    return { "access_token": access_token}
