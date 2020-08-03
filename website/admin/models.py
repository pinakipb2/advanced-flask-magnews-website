from website import db

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile = db.Column(db.String(180), default='profile.jpg')
    date = db.Column(db.DateTime, nullable=True)
    activate = db.Column(db.Boolean, nullable=False, default=False)
    twostep = db.Column(db.Boolean, nullable=False, default=False)
    darkmode = db.Column(db.Boolean, nullable=False, default=False)
    apikey = db.Column(db.String(120), unique=True, nullable=False)
    
class Admincode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100),unique=True,nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    

