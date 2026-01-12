from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas
from auth import get_password_hash 
from datetime import date, timedelta


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, password=hashed_password, created_at=date.today())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_token(db: Session, user: models.User, token: str | None):
    user.refresh_token = token
    db.commit()



def create_contact(db: Session, contact: schemas.ContactCreate, user: models.User):
   
    db_contact = models.Contact(**contact.model_dump(), user_id=user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, user: models.User, skip: int = 0, limit: int = 100, query: str = None):
   
    sql_query = db.query(models.Contact).filter(models.Contact.user_id == user.id)
    
    if query:
        search = f"%{query}%"
        sql_query = sql_query.filter(
            or_(
                models.Contact.first_name.ilike(search),
                models.Contact.last_name.ilike(search),
                models.Contact.email.ilike(search)
            )
        )
    return sql_query.offset(skip).limit(limit).all()

def get_contact_by_id(db: Session, contact_id: int, user: models.User):
  
    return db.query(models.Contact).filter(models.Contact.id == contact_id, models.Contact.user_id == user.id).first()

def update_contact(db: Session, contact_id: int, contact_update: schemas.ContactUpdate, user: models.User):
    db_contact = get_contact_by_id(db, contact_id, user)
    if db_contact:
        for key, value in contact_update.model_dump(exclude_unset=True).items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, user: models.User):
    db_contact = get_contact_by_id(db, contact_id, user)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def get_upcoming_birthdays(db: Session, user: models.User):
    today = date.today()
    end_date = today + timedelta(days=7)
    
   
    contacts = db.query(models.Contact).filter(models.Contact.user_id == user.id).all()
    upcoming = []
    
    for contact in contacts:
        bday_this_year = contact.birthday.replace(year=today.year)
        if bday_this_year < today:
            bday_this_year = bday_this_year.replace(year=today.year + 1)
        if today <= bday_this_year <= end_date:
            upcoming.append(contact)
    return upcoming