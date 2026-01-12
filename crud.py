from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Contact
from schemas import ContactCreate, ContactUpdate
from datetime import date, timedelta

def create_contact(db: Session, contact: ContactCreate):
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contacts(db: Session, skip: int = 0, limit: int = 100, query: str = None):
    sql_query = db.query(Contact)
    
    if query:
        search = f"%{query}%"
        sql_query = sql_query.filter(
            or_(
                Contact.first_name.ilike(search),
                Contact.last_name.ilike(search),
                Contact.email.ilike(search)
            )
        )
        
    return sql_query.offset(skip).limit(limit).all()

def get_contact_by_id(db: Session, contact_id: int):
    return db.query(Contact).filter(Contact.id == contact_id).first()

def get_contact_by_email(db: Session, email: str):
    return db.query(Contact).filter(Contact.email == email).first()

def update_contact(db: Session, contact_id: int, contact_update: ContactUpdate):
    db_contact = get_contact_by_id(db, contact_id)
    if db_contact:
        update_data = contact_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_contact, key, value)
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int):
    db_contact = get_contact_by_id(db, contact_id)
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def get_upcoming_birthdays(db: Session):
    today = date.today()
    end_date = today + timedelta(days=7)
    
    contacts = db.query(Contact).all()
    upcoming_birthdays = []
    
    for contact in contacts:
        bday_this_year = contact.birthday.replace(year=today.year)
        
        if bday_this_year < today:
            bday_this_year = contact.birthday.replace(year=today.year + 1)
            
        if today <= bday_this_year <= end_date:
            upcoming_birthdays.append(contact)
            
    return upcoming_birthdays