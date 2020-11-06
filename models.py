# models.py
import flask_sqlalchemy
from app import db

class User1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    picture = db.Column(db.String(350))
    room = db.Column(db.String(120))
    
    def __init__(self, name, email, picture, room):
        self.name = name
        self.email = email
        self.picture = picture
        self.room = room
        
    def __repr__(self):
        return "<Name: {}\nemail: {}\npicture: {}\nroom: {}".format(self.name, self.email, self.picture, self.room)