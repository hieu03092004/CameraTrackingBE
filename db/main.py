from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal, get_db
from . import models, schemas

# Tạo bảng
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
