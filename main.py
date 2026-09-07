from fastapi import FastAPI, HTTPException, Depends, Path,Query,Body, UploadFile, \
    File,Form,status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import JWTError, jwt
from fastapi.responses import FileResponse
from PIL import Image
from typing import Optional, List,Dict, Annotated
import sqlite3
from sqlalchemy.orm import Session
from  models import Base, User, Post, Item, Rates
from database import engine, Session_local
import requests
from schemas import UserCreate, User as DbUser, PostCreate, PostResponse,\
    ItemCreate,ItemResponse,RateResponse, RateCreate, UserUpdate,UserPatch,ItemPatch,PostUpdate,PostBase,\
    UserRegister,Token
import os
from uuid import uuid4
from auth import(
    SECRET_KEY,
    ALGORITHM,
    hash_password,
    verify_password,
    create_access_token
)


UPLOAD_DIR ="Uploads"
COMPRESSED_DIR="compressed"

os.makedirs(UPLOAD_DIR, exist_ok= True)
os.makedirs(COMPRESSED_DIR, exist_ok= True)

app = FastAPI()

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")
Base.metadata.create_all(bind=engine)





def get_db():
    db =Session_local()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_model=List[DbUser], description="Title for Site")
def title_suit(db: Session = Depends(get_db)):
    names = db.query(User)
    return names



@app.post("/register", response_model=DbUser)
async def register(
    user : UserRegister,
    db : Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user is not None:
        raise HTTPException(status_code= 400, detail="Email already registered")
    new_user = User(
        name=user.name,
        age=user.age,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login", response_model= Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session=Depends(get_db)):

    user = db.query(User).filter(User.email == form_data.username).first()

    if user is None:
        raise HTTPException(status_code = 401, detail="Incorrect email or password")

    if not verify_password(form_data.password,user.hashed_password):
        raise HTTPException(status_code= 401, detail="Incorrect email or password")
    access_token = create_access_token(data = {"sub":str(user.id)})

    return {
        "access_token":access_token,
        "token_type":"bearer"
    }

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    credentials_excception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,
                                           detail= "Could not validate credentials",
                                           headers={"WWW-Authenticate" : "Bearer"},)

    try:
        payload = jwt.decode(token,
                             SECRET_KEY,
                             algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_excception
    except JWTError:
        raise credentials_excception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_excception
    return user

@app.get("/me", response_model= DbUser)
async def get_me(
    current_user: User = Depends(get_current_user)):
    return current_user


@app.post('/users/', response_model=DbUser)
async def create_user(user: UserCreate, db: Session = Depends(get_db)) -> User:
    db_user = User(name = user.name, age = user.age)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@app.get('/users/',response_model=List[DbUser])
async def users(
    db: Session=Depends(get_db)):
    return db.query(User).limit(10).offset(0).all()

@app.get('/users/search', response_model=List[DbUser])
async def search_users(
    name: Optional[str] = Query(None, description="Поиск по имени"),
    age: Optional[str] = Query(None, description="Фильтр по году"),
    db: Session= Depends(get_db)):
    query = db.query(User)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if age:
        query = query.filter(User.age.ilike(f"{age}"))

    results = query.all()

    if not results:
        raise HTTPException(status_code = 404, detail= "Not found")

    return query

@app.get('/users/{user_id}',response_model=DbUser)
async def get_users(
    user_id: int, 
    db: Session=Depends(get_db)):
    user = db.query(User).filter(user_id == User.id).first()

    if user is None:
        raise HTTPException(status_code = 404, detail="User not Found")
    return user



@app.put("/users/{user_id}", response_model=DbUser)
async def update_user(
    user_id: int,
    user_date: UserUpdate,
    db : Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail = "User not found")
    user.name = user_date.name
    user.age = user_date.age
    user.email = user_date.email
    db.commit()
    db.refresh(user)
    return user

@app.patch("/users/{user_id}",response_model=DbUser)
async def patch_user(
    user_id : int,
    user_data : UserPatch,
    db : Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code = 404, detail="User not Found")
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.age is not None:
        user.age = user_data.age
    if user_data.email is not None:
            user.email = user_data.email

    db.commit()
    db.refresh(user)
    return user

@app.delete('/users/{user_id}')
async def delete_user(user_id: int, db : Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:

        raise HTTPException(status_code= 404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message":"User deleted"}


@app.post('/posts/', response_model=PostResponse)
async def create_post(post: PostCreate, db: Session = Depends(get_db),
                      current_user: User=Depends(get_current_user)):
    
        
    db_post = Post(title=post.title, body=post.body, author_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    return db_post


@app.get('/posts/', response_model=List[PostResponse])
async def posts(
    limit: int = 10,
    offset: int = 0,
    db: Session= Depends(get_db)):

    post = db.query(Post).offset(offset).limit(limit).all()
    return post

@app.get('/posts/', response_model=list[PostResponse])
async def get_posts_filt(
    
    author_id: Optional[int] = Query(None, description="Фильтр по ID автора"),
    db: Session = Depends(get_db)
):
    query = db.query(Post)

    
    if author_id is not None:
       
        query = query.filter(Post.author_id == author_id)

    results = query.all()
    
    return results

@app.get('/posts/search', response_model=List[PostResponse])
async def search_post(
    q: Optional[str] = Query(None, description="Поиск по заголовку"),
    body: Optional[str] = Query(None, description="Фильтр по телу"),
    db: Session= Depends(get_db)):
    query = db.query(Post)

    if q:
        query = query.filter(Post.title.ilike(f"%{q}%"))
    if body:
        query = query.filter(Post.body.ilike(f"%{body}%"))

    results = query.all()

    if not results:
        raise HTTPException(status_code = 404, detail= "Not found")

    return query

    

@app.get('/posts/{post_id}', response_model=PostResponse)
async def get_posts(
    post_id : int,
    db: Session= Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code = 404, detail= "Post not found")

    return post

@app.put("/posts/{post_id}", response_model=PostBase)
async def update_post(
    post_id: int,
    post_date: PostUpdate,
    db : Session = Depends(get_db)):

    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail = "post not found")
    post.title = post_date.title
    post.body = post_date.body
    db.commit()
    db.refresh(post)
    return post


@app.delete('/posts/{post_id}')
async def delete_post(post_id: int, db : Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if post is None:

        raise HTTPException(status_code= 404, detail="post not found")

    db.delete(post)
    db.commit()
    return {"message":"item deleted"}

@app.patch("/post/{post_id}", response_model= PostResponse)
async def patch_post(
    post_id : int,
    post_data : ItemPatch,
    db : Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if post is None:
        raise HTTPException(status_code = 404, detail = "post is not found") 

    if post_data.title is not None:
        post.title = post_data.title
    if post_data.body is not None:
        post.body = post_data.body
    db.commit()
    db.refresh(post)
    return post


@app.post('/items/', response_model=ItemResponse)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)) -> Item:

    db_item = db.query(User).filter(User.id ==item.author_id).first()

    if db_item is None:
        raise HTTPException(status_code=404, detail='User not found')
    db_item = Item(title = item.title, body = item.body, author_id = item.author_id)
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item

@app.get('/items/', response_model=List[ItemResponse])
async def items(db: Session= Depends(get_db)):
    return db.query(Item).all()


@app.get('/items/search', response_model=List[ItemResponse])
async def search_items(
    title: Optional[str] = None,
    db: Session= Depends(get_db)):
    query = db.query(Item)

    if title:
        query = query.filter(Item.title.ilike(f"%{title}%"))

    results = query.all()

    if not results:
        raise HTTPException(status_code = 404, detail= "Not found")

    return query.all()

@app.get('/items/{items_id}', response_model=ItemResponse)
async def get_item(
    items_id : int,    
    db: Session= Depends(get_db)):
    item  = db.query(Item).filter(Item.id == items_id).first()

    if item is None:
        raise HTTPException(status_code = 404, detail = "Item Not Fount")
    return item

@app.patch("/items/{item_id}", response_model= ItemResponse)
async def patch_item(
    item_id : int,
    item_data : ItemPatch,
    db : Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()

    if item is None:
        raise HTTPException(status_code = 404, detail = "Item is not found") 

    if item_data.title is not None:
        item.title = item_data.title
    if item_data.body is not None:
        item.body = item_data.body
    db.commit()
    db.refresh(item)
    return item

@app.delete('/items/{item_id}')
async def delete_item(item_id: int, db : Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()

    if item is None:

        raise HTTPException(status_code= 404, detail="item not found")

    db.delete(item)
    db.commit()
    return {"message":"item deleted"}


@app.post('/rates/', response_model=RateResponse)
async def create_rate(rate: RateCreate, db: Session = Depends(get_db)):
    db_rate = Rates(usd = rate.usd, rub = rate.rub )
    db.add(db_rate)
    db.commit()
    db.refresh(db_rate)

    return db_rate



@app.post("/rates/update")
async def update_rate(db: Session = Depends(get_db)):
        
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url)
    
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Currency API is not available")
    
        data = response.json()
    
        rub_rate = round(data["rates"]["RUB"],2)

        db_rate = Rates(
            
            usd = 1.0,
            rub = rub_rate
        )
        db.add(db_rate)
        db.commit()
        db.refresh(db_rate)

        return db_rate


@app.get('/rates/',response_model=List[RateResponse])
async def rates(db: Session=Depends(get_db)):
    return db.query(Rates).all()


@app.get('/rates/live/')
async def get_live_rate():
    url = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Currency API is not available")

    data = response.json()

    rub_rate = round(data["rates"]["RUB"],2)

    return {
        "base":"USD",
        "target":"RUB",
        "rate": rub_rate
    }


@app.delete('/rates/{rate_id}')
async def delete_rate(rate_id: int, db : Session = Depends(get_db)):
    rate = db.query(Rates).filter(Rates.id == rate_id).first()

    if rate is None:

        raise HTTPException(status_code= 404, detail="Rate not found")

    db.delete(rate)
    db.commit()
    return {"message":"Rate deleted"}

    
@app.post("/compress-image")
async def compress_image(
    file: UploadFile=File(...),
    quality: int=Form(70)):
    if quality < 1 or quality > 100:
        raise HTTPException(status_code=400, detail="Quality must be between 1 and 100")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code= 400, detail="File must be an image")
    file_extension = file.filename.split(".")[-1].lower()

    if file_extension not in ["jpg","jpeg","png"]:
        raise HTTPException(status_code= 400, detail="Only JPG, JPEG and PNG files are supported")

    unique_name = f"{uuid4}.{file_extension}"
    upload_path = os.path.join(UPLOAD_DIR, unique_name)

    with open (upload_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    original_size = os.path.getsize(upload_path)
    compressed_fillname = f"compressed_{unique_name}"
    compressed_parh = os.path.join(COMPRESSED_DIR,compressed_fillname)

    try:
        image = Image.open(upload_path)
        if image.mode in ("RGBA","P"):
            image = image.convert("RGB")
        image.save(compressed_parh,
                   Optimize=True,
                   quality=quality)

    except Exception:
        raise HTTPException(status_code = 500, detail="Could not process image")
    compressed_size = os.path.getsize(compressed_parh)
    compression_percent = (
        (original_size - compressed_size/original_size)*100
    )
    return {
        "fillname": file.filename,
        "original_size_kb":round(original_size/1024,2),
        "compressed_sixe_kb":round(compressed_size/1024,2),
        "compression_percent":round(compression_percent,2),
        "download_url":f"/files/{compressed_fillname}"

    }


@app.get("/files/{filename}")
def download_file(filename: str):
    file_path = os.path.join(COMPRESSED_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code = 404, detail="file not found")
    return FileResponse(path = file_path,
                        fillname = filename,
                        media_type="application/octet-stream"
                        )


@app.get("/health")
def health_check():
    return {"status":"ok"}
 
