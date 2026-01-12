from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(Date)
    refresh_token = Column(String, nullable=True)

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, index=True) # Email контакту (не унікальний глобально, бо різні юзери можуть мати один контакт)
    phone_number = Column(String)
    birthday = Column(Date)
    additional_info = Column(String, nullable=True)
    
    # Зв'язок з користувачем (власником контакту)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="contacts")