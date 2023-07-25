from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import generate_pairs
from flask_sqlalchemy import SQLAlchemy
from app.config import create_app
from sqlalchemy.orm import Query
from typing import List, Tuple
from sqlalchemy import DECIMAL
import datetime
import random
import uuid
from dotenv import load_dotenv
from os import getenv
import jwt
from flask_cors import CORS
from enum import Enum

app = create_app()
db = SQLAlchemy(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})




    
class BaseModel(db.Model):
    __abstract__ = True
    __tablename__ = ''

    query: Query


class User(BaseModel):
    __tablename__ = 'user'
    id = db.Column(db.String(32), primary_key=True, default=lambda: str(uuid.uuid4().hex))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def generate_access_token(self):
        secret_key = getenv('SECRET_KEY')
        payload = {
            'id': self.id,
            'exp': (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).timestamp()
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

    def generate_recovery_token(self):
        secret_key = getenv('SECRET_KEY')
        
        payload = {
            'id': self.id,
            'exp': (datetime.datetime.utcnow() + datetime.timedelta(days=1)).timestamp()
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

    

    

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password
    
    def __repr__(self):
        return '<User %r>' % self.name
    
    def serialize(self):
        return {
            'id': self.id,
            'username': self.name,
            'email': self.email
        }
    


class Group(BaseModel):
    __tablename__ = 'group'


    
    id = db.Column(db.String(32), primary_key=True,default=lambda: str(uuid.uuid4().hex))
    description = db.Column(db.String(80), nullable=False)
    creator = db.Column(db.String(32), db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())
    event_date = db.Column(db.DateTime)
    min_gift_price = db.Column(DECIMAL(10,2))
    max_gift_price = db.Column(DECIMAL(10,2))
    drawn = db.Column(db.String(10), nullable=False, default='NO')

    def __init__(self, description, creator, event_date, min_gift_price, max_gift_price):
        self.description = description
        self.creator = creator
        self.event_date = event_date
        self.min_gift_price = min_gift_price
        self.max_gift_price = max_gift_price

    friends = db.relationship('Friend', backref='group', lazy='joined')
    
    def imperfect_drawn(self):
        pairs = generate_pairs(len(self.friends))
        for pair in pairs:                
            self.friends[pair[0]].friend_id = self.friends[pair[1]].user_id
        self.drawn = 'IMPERFECT'
        db.session.commit()

    def perfect_drawn(self):
        random.shuffle(self.friends)
        for i in range(len(self.friends)-1):
            self.friends[i].friend_id = self.friends[i+1].user_id
        self.friends[-1].friend_id = self.friends[0].user_id
        self.drawn = 'PERFECT'
        db.session.commit()
    
    def kick_out(self, friend_id):
        friend = Friend.query.filter_by(user_id=friend_id).first()
        db.session.delete(friend)
        db.session.commit()

        



    def serialize(self):

        return {
            'id': self.id,
            'description': self.description,
            'creator': self.creator,
            'event_date': self.event_date.strftime('%Y-%m-%d %H:%M:%S'),
            'min_gift_price': self.min_gift_price.__str__(),
            'max_gift_price': self.max_gift_price.__str__(), 
            'friends': [friend.serialize() for friend in self.friends]
        }
    def su_serialize(self):
        return {
            'id': self.id,
            'description': self.description,
            'creator': self.creator,
            'event_date': self.event_date.strftime('%Y-%m-%d %H:%M:%S'),
            'min_gift_price': self.min_gift_price.__str__(),
            'max_gift_price': self.max_gift_price.__str__(), 
            'friends': [friend.su_serialize() for friend in self.friends]
        }

    def __repr__(self):
        return '<Group %r>' % self.description

class Friend(BaseModel):
    __tablename__ = 'friend'
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'), primary_key=True)
    group_id = db.Column(db.String(32), db.ForeignKey('group.id'), primary_key=True)
    friend_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=True, default=None)
    gift_desired = db.Column(db.String(80))
    is_admin = db.Column(db.Boolean, default=False) 

    def __init__(self, user_id, group_id, gift_desired):
        self.user_id = user_id
        self.group_id = group_id
        self.gift_desired = gift_desired

    def su_serialize(self):
        user_name = db.session.query(User).filter_by(id=self.user_id).first().name
        friend = db.session.query(User).filter_by(id=self.friend_id).first()

        return {
            'user_id': self.user_id,
            'user_name': user_name,
            'group_id': self.group_id,
            'gift_desired': self.gift_desired,
            'friend_name': friend.name if friend else None,
            'friend_id': self.friend_id,
            'is_admin': self.is_admin
        }
    
    def serialize(self):
        user_name = db.session.query(User).filter_by(id=self.user_id).first().name
        friend = db.session.query(User).filter_by(id=self.friend_id).first()

        return {
            'user_id': self.user_id,
            'user_name': user_name,
            'group_id': self.group_id,
            'gift_desired': self.gift_desired,
            'friend_name': friend.name if friend else None,
            'friend_id': 'unauthorized',
            'is_admin': self.is_admin
        }
    

    def __repr__(self):
        return f'<Friend user_id={self.user_id}>'

    
