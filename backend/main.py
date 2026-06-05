import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel
import passlib.hash
import jwt
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/notes.db")
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(200))

class NoteModel(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    content = Column(Text)
    icon_path = Column(String(500), nullable=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notes API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.getenv("JWT_SECRET", "supersecret123")
JWT_ALGORITHM = "HS256"

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Helpers
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")


class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    icon_path: Optional[str] = None
    class Config:
        from_attributes = True

# WebSockets Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/register")
@limiter.limit("5/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = passlib.hash.bcrypt.hash(user.password)
    db_user = UserModel(username=user.username, password_hash=hashed)
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if not db_user or not passlib.hash.bcrypt.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    
    access_token_expires = timedelta(minutes=60)
    expire = datetime.utcnow() + access_token_expires
    to_encode = {"sub": db_user.username, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}

@app.get("/notes", response_model=List[NoteResponse])
def get_notes(request: Request, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(NoteModel).order_by(NoteModel.id.desc()).all()

@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    icon: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    icon_path = None
    if icon:
        file_ext = icon.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(icon.file, buffer)
        icon_path = f"/static/icons/{unique_name}"
        
    db_note = NoteModel(title=title, content=content, icon_path=icon_path)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    # Notify via WebSocket
    await manager.broadcast(f"New note added: {title}")
    
    return db_note

@app.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    request: Request,
    note_id: int,
    title: str = Form(...),
    content: str = Form(""),
    icon: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")

    db_note.title = title
    db_note.content = content

    if icon:
        if db_note.icon_path:
            old_filename = db_note.icon_path.split("/")[-1]
            old_filepath = os.path.join("uploads", old_filename)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

        file_ext = icon.filename.split('.')[-1]
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_name)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(icon.file, buffer)
        db_note.icon_path = f"/static/icons/{unique_name}"

    db.commit()
    db.refresh(db_note)

    await manager.broadcast(f"Note updated: {db_note.title}")
    return db_note

@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(request: Request, note_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    if db_note.icon_path:
        filename = db_note.icon_path.split("/")[-1]
        filepath = os.path.join("uploads", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
    db.delete(db_note)
    db.commit()
    return None
