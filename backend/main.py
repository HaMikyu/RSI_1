import os
import shutil
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/notes.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class NoteModel(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    content = Column(Text)
    icon_path = Column(String(500), nullable=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    icon_path: Optional[str] = None
    
    class Config:
        from_attributes = True

@app.get("/notes", response_model=List[NoteResponse])
def get_notes(db: Session = Depends(get_db)):
    """Fetch all notes"""
    return db.query(NoteModel).order_by(NoteModel.id.desc()).all()

@app.post("/notes", response_model=NoteResponse)
def create_note(
    title: str = Form(...),
    content: str = Form(""),
    icon: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Create a new note, optionally with an icon"""
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
    return db_note

@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
        
    if db_note.icon_path:
        # Extract filename from path '/static/icons/xyz.ext'
        filename = db_note.icon_path.split("/")[-1]
        filepath = os.path.join("uploads", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
    db.delete(db_note)
    db.commit()
    return None
