from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import crud
import auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts API with Auth")


@app.post("/auth/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/auth/login", response_model=schemas.Token, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерація токенів
    access_token = auth.create_access_token(data={"sub": user.email})
    refresh_token = auth.create_refresh_token(data={"sub": user.email})
    
    # Зберігаємо refresh_token в БД
    crud.update_token(db, user, refresh_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.get("/auth/refresh_token", response_model=schemas.Token, tags=["auth"])
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = auth.jwt.decode(refresh_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except auth.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = crud.get_user_by_email(db, email)
    if user is None or user.refresh_token != refresh_token:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    new_access_token = auth.create_access_token(data={"sub": email})
    new_refresh_token = auth.create_refresh_token(data={"sub": email})
    crud.update_token(db, user, new_refresh_token)
    
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@app.post("/contacts/", response_model=schemas.ContactResponse, status_code=status.HTTP_201_CREATED, tags=["contacts"])
def create_contact(
    contact: schemas.ContactCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_contact(db=db, contact=contact, user=current_user)

@app.get("/contacts/", response_model=List[schemas.ContactResponse], tags=["contacts"])
def read_contacts(
    skip: int = 0, 
    limit: int = 100, 
    q: str = Query(None), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    contacts = crud.get_contacts(db, user=current_user, skip=skip, limit=limit, query=q)
    return contacts

@app.get("/contacts/upcoming-birthdays", response_model=List[schemas.ContactResponse], tags=["contacts"])
def get_birthdays(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    contacts = crud.get_upcoming_birthdays(db, user=current_user)
    return contacts

@app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse, tags=["contacts"])
def read_contact(
    contact_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_contact = crud.get_contact_by_id(db, contact_id, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.put("/contacts/{contact_id}", response_model=schemas.ContactResponse, tags=["contacts"])
def update_contact(
    contact_id: int, 
    contact_update: schemas.ContactUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_contact = crud.update_contact(db, contact_id, contact_update, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.delete("/contacts/{contact_id}", response_model=schemas.ContactResponse, tags=["contacts"])
def delete_contact(
    contact_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_contact = crud.delete_contact(db, contact_id, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.get("/", tags=["root"])
def read_root():
    return {"message": "Contacts API with Auth is running"} 