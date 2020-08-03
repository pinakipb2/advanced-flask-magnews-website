from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from flask_msearch import Search
from flask_uploads import IMAGES,UploadSet,configure_uploads,patch_request_class


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

basedir = os.path.abspath(os.path.dirname(__file__))
local_server=True
app = Flask(__name__)
app.secret_key = 'magnewskey'
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'static/images/bugscreenshots')
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)
search = Search()
search.init_app(app)


#app.config['SECRET_KEY'] = 'jksdfbsvjhshkadfkjhvdfgxvhgsjkxfhvsbfhvgsdjkhkhvsdufkjhl'

from website.admin import routes
from website.user import routes
from website.body import routes
# Werkzeug==0.15.6