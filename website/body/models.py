from website import db
from website.user.models import User
from website.admin.models import Admin

class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    website = db.Column(db.String(120), nullable=False)
    message = db.Column(db.String(6000), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    
''' class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    body = db.Column(db.String(6000), nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('posts',lazy=True))
    image = db.Column(db.String(150), nullable=False, default='blog-list-01.jpg')
    user_id = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(60), nullable=False)
    views = db.Column(db.Integer,default=0,nullable=False)
    comments = db.Column(db.Integer,default=0,nullable=False)
    feature = db.Column(db.String(20), default=1, nullable=False)
    date_pub = db.Column(db.String(120), nullable=True) '''


class Blogpost(db.Model):
    __searchable__=['title','body']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    body = db.Column(db.String(6000), nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey('category.id',ondelete='CASCADE'),nullable=False)
    category = db.relationship('Category',backref=db.backref('post',lazy=True))
    image = db.Column(db.String(150), nullable=False, default='blog-list-01.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('authors.id', ondelete='CASCADE'), nullable=False)
    author = db.relationship('Authors', backref=db.backref('post',lazy=True, passive_deletes=True))
    views = db.Column(db.Integer,default=0,nullable=False)
    date_pub = db.Column(db.DateTime, nullable=True)
    rough_id = db.Column(db.Integer,nullable=True)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    body = db.Column(db.String(6000), nullable=False)
    category_id = db.Column(db.Integer,db.ForeignKey('category.id',ondelete='CASCADE'),nullable=False)
    category = db.relationship('Category',backref=db.backref('allpost',lazy=True))
    image = db.Column(db.String(150), nullable=False, default='blog-list-01.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('authors.id', ondelete='CASCADE'), nullable=False)
    author = db.relationship('Authors', backref=db.backref('allpost',lazy=True, passive_deletes=True))
    date_pub = db.Column(db.DateTime, nullable=True)
    draft = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.Integer,nullable=True,default=None)
    fair_id = db.Column(db.Integer,nullable=True)
    
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    
class Authors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile = db.Column(db.String(180),  default="profile.jpg")
    date = db.Column(db.DateTime, nullable=True)
    
class Bugreport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sub_date = db.Column(db.DateTime, nullable=True)
    submitted_by = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    bug_desc = db.Column(db.String(120), nullable=False)
    bug_url = db.Column(db.String(120), nullable=False)
    platform = db.Column(db.String(80), nullable=False)
    browser = db.Column(db.String(80), nullable=False)
    bug_date = db.Column(db.String(120), nullable=False)
    scrnshot = db.Column(db.String(80), nullable=True)
    expected_res = db.Column(db.String(120), nullable=True)
    actual_res = db.Column(db.String(120), nullable=True)
    frequency = db.Column(db.String(80), nullable=False)
    priority =  db.Column(db.String(80), nullable=False)
    status = db.Column(db.Integer, default=0)
    
class UserToAdmins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    users = db.relationship('User', backref=db.backref('post',lazy=True, passive_deletes=True))
    subject = db.Column(db.String(6000), nullable=False)
    message = db.Column(db.String(6000), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False)
    
class AdminToAllUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id', ondelete='CASCADE'), nullable=False)
    admins = db.relationship('Admin', backref=db.backref('post',lazy=True, passive_deletes=True))
    subject = db.Column(db.String(6000), nullable=False)
    message = db.Column(db.String(6000), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    
class AdminToUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id', ondelete='CASCADE'), nullable=False)
    admins = db.relationship('Admin', backref=db.backref('mydb',lazy=True, passive_deletes=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    users = db.relationship('User', backref=db.backref('mydb',lazy=True, passive_deletes=True))
    subject = db.Column(db.String(6000), nullable=False)
    message = db.Column(db.String(6000), nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False)
    
    
