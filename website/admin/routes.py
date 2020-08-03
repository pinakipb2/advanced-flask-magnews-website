from website import app,db
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mail import Mail
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import func
import math
import os
import os.path
import secrets
from .models import Admin,Admincode
from website.body.models import Blogpost,Category,Authors,Bugreport,Contact,UserToAdmins,AdminToAllUsers,AdminToUser,Posts
from website.user.models import User
import json
#from sqlalchemy import create_engine
import cv2
from flask_bcrypt import Bcrypt
import smtplib
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(app, key_func = get_remote_address)

SECRET_KEY = 'my_secret_key'
SALT = 'my_password_salt'
MAIL_SERVER = 'smtp.gmail.com:587'

with open('adminconfig.json', 'r') as c:
    params = json.load(c)["params"]


app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config['ADMINDP_UPLOAD_FOLDER'] = params['admindp_upload_location']
bcrypt = Bcrypt(app)



#after 3 days the session will be logged out automatically
app.permanent_session_lifetime = timedelta(days=3)


class Mailstore():
    myemail = None
    otp = None
    pwd = None
    uuid_url = None
    resend_url = None
    tsv_otp = None
    
myVar = Mailstore()



def generate_confirmation_token(email, username):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    print('serializer',serializer)
    return serializer.dumps({'email': email, 'username': username}, salt=SALT)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        result = serializer.loads(token, salt=SALT, max_age=expiration)
    except:
        return False
    return result


def check_email_validation(email):
    print('email', email)
    result = email.endswith('.com')
    return result


def send_mail(email, template):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email
            
    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: Confirm your account on MagNews",
        "",
        "Thanks for signing up with MagNews! You must follow this link to activate your account: ",
        "",
        template,
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return


def send_confirmation_mail(email, username):
    token = generate_confirmation_token(email, username)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('admin/registration/activate.html', confirm_url=confirm_url)
    send_mail(email, html)
    return


@app.route('/admin-register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        admin_code = request.form.get('admin_code')
        check_user = Authors.query.filter_by(username=username).first()
        if check_user:
            flash("The username already exists!",'danger')
            return redirect(url_for('admin_register'))
        check_email = Authors.query.filter_by(email=email).first()
        if check_email:
            flash("The email id already exists!",'danger')
            return redirect(url_for('admin_register'))
        check_code = Admincode.query.filter_by(code=admin_code).first()
        if not check_code:
            flash("The code you have entered is wrong recheck and try again!",'danger')
            return redirect(url_for('admin_register'))
        if password != re_password :
            flash("Password do not match please check and try again!",'danger') 
            return redirect(url_for('admin_register'))
        if check_email_validation(email):
            password_hash = bcrypt.generate_password_hash(password)
            api = secrets.token_hex(17)
            new_user = Admin(name=fullname,username=username,email=email,password=password_hash,profile='profile.jpg',date=datetime.now(),activate=False,twostep=False,darkmode=False,apikey=api)
            db.session.add(new_user)
            db.session.commit()
            myVar.uuid_url = uuid.uuid4()
            send_confirmation_mail(email, username)
            return redirect(url_for('admin_congratulations',id=myVar.uuid_url))
        else:
            myVar.uuid_url = uuid.uuid4()
            return redirect(url_for('admin_email_not_valid',id=myVar.uuid_url))
    return render_template('admin/admin-register.html',params=params)


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        data = confirm_token(token)
    except:
        return redirect(url_for('admin_token_expired'))
    if(data==False):
        return redirect(url_for('admin_token_expired'))
    user = Admin.query.filter_by(username=data['username']).first()
    if user:
        if (user.activate==False):
            user.activate=True
            db.session.add(user)
            db.session.commit()
            new_author = Authors(name=user.name,username=user.username,email=user.email,profile=user.profile,date=datetime.now())
            db.session.add(new_author)
            db.session.commit()
        else:
            return redirect(url_for('admin_already_verified'))
    myVar.uuid_url = uuid.uuid4()
    return redirect(url_for('admin_verified',id=myVar.uuid_url))


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if('admin_username' in session and 'admin_email' in session):
        return redirect(url_for('admin_dash'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = Admin.query.filter_by(email=email).first()
        if not user:
            flash('User does not exist!','danger')
            return redirect(url_for('admin_login'))
        check_pass = bcrypt.check_password_hash(user.password,password)
        if not check_pass:
            flash('Password do not match, try again!','warning')
            return redirect(url_for('admin_login'))
        if(user.twostep==0):
            session.permanent = True
            session['admin_username'] = user.username
            session['admin_email'] = user.email
            if user.activate is False:
                return redirect(url_for('admin_unconfirmed'))
            flash('You are now logged in to the dashboard!','success')
            return redirect(url_for('admin_dash'))
        else:
            myVar.myemail = user.email
            myVar.tsv_otp = secrets.token_hex(5)
            admin_tsv_otp(user.email)
            return redirect(url_for('admin_twostep_otp'))
    return render_template('admin/admin-login.html',params=params)


@app.route('/admin-logout', methods=['GET','POST'])
def admin_logout():
    if('admin_username' in session and 'admin_email' in session):
        del session['admin_username']
        del session['admin_email']
        return redirect(url_for('admin_login'))
    else:
        return redirect(url_for('home'))

@app.route('/admin-resend')
def resend_confirmation():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            #return redirect(url_for('admin_unconfirmed'))
            send_confirmation_mail(session['admin_email'], session['admin_username'])
            del session['admin_username']
            del session['admin_email']
            myVar.resend_url = uuid.uuid4()
            return redirect(url_for('admin_congratulations',id=myVar.resend_url))
        else:
            return redirect(url_for('admin_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)
    
@app.route('/admin-resend-cancel')
def resend_confirmation_cancel():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            del session['admin_username']
            del session['admin_email']
            return redirect(url_for('admin_register'))
        else:
            return redirect(url_for('admin_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if('admin_username' not in session and 'admin_email' not in session):
        if request.method =='POST':
            username = request.form.get('username')
            email = request.form.get('email')
            user = Admin.query.filter_by(username=username).first()
            if (not user):
                flash('Username does not exists','danger')
            elif(not user.email==email):
                flash('Email does not match with the username','danger')
            else:
                myVar.myemail = email
                myVar.otp = secrets.token_hex(10)
                admin_pwd_reset_mail(email)
                flash('OTP has been sent in your e-mail!','success')
                return redirect(url_for('admin_otp'))
        return render_template('/admin/admin-forgot-pass.html',params=params)
    if('admin_username'  in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))


@app.route('/admin/otp', methods=['GET', 'POST'])
def admin_otp():
    if('admin_username' not in session and 'admin_email' not in session):
        if request.method == 'POST':
            otp = request.form.get('otp')
            if(myVar.otp!=otp):
                flash('The OTP you have entered is incorrect!','danger')
                return redirect(url_for('admin_otp'))
            if (myVar.otp==otp):
                user = Admin.query.filter_by(email=myVar.myemail).first()
                myVar.pwd = secrets.token_hex(7)
                new_pass = bcrypt.generate_password_hash(myVar.pwd)
                user.password = new_pass
                db.session.commit()
                admin_new_pwd(myVar.myemail)
                myVar.otp = None
                myVar.myemail = None
                myVar.pwd = None
                flash('New password has been sent through mail.','success')
                return redirect(url_for('admin_login'))
        return render_template('/admin/pwd-reset-otp.html',params=params)
    if('admin_username'  in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))


def admin_pwd_reset_mail(email):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: OTP for password reset of your account on MagNews",
        "",
        "Your otp for the reset of your Magnews account password :",
        "",
        myVar.otp,
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return

def admin_create_user(email,uname,pwd):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: Welcome to MagNews!",
        "",
        "A new account has been created on MagNews",
        "",
        "Username : " + uname,
        "Password : " + pwd,
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return


def admin_new_pwd(email):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: New Password of your account on MagNews",
        "",
        "Your new password for your Magnews account is :",
        "",
        myVar.pwd,
        "",
        "You can reset it anytime from Admin Dashboard.",
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return


def admin_changed_pwd(email):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: Password changed for your account on MagNews",
        "",
        "Your password for your Magnews account has been changed recently. If it was not you, you can the password soon using forgot password.",
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return


def admin_tsv_otp(email):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: OTP for two-step verification of your account on MagNews",
        "",
        "OTP for two-step verification for your Magnews account is :",
        "",
        myVar.tsv_otp,
        "",
        "You can disable two-step verification anytime from your Magnews profile page.",
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return

def admin_tsv_activated(email):
    with open('email.txt', 'r') as f1:
        with open('key.txt', 'r') as f2:
            username = f1.readline()
            password = f2.readline()
            _from = f1.readline()
            _to = email

    msg = "\r\n".join([
        "From: " + _from,
        "To: " + email,
        "Subject: Two-step verification settings for your account on MagNews",
        "",
        "Two-step verification settings for your account on MagNews has been changed.",
        "",
        "You can disable or enable two-step verification anytime from your Magnews profile page.",
        "",
        "Have fun, and don't hesitate to contact us with your feedback.",
        "",
        "The MagNews Team."
    ])
    server = smtplib.SMTP(MAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(_from, _to, msg)
    server.quit()
    return


@app.route('/admin/dashboard')
def admin_dash():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('admin_unconfirmed'))
        post_cnt = Blogpost.query.count()
        cat_cnt = Category.query.count()
        auth_cnt = User.query.count()
        bugreport_cnt = Bugreport.query.count()
        mail_senders = User.query.join(UserToAdmins,(User.id == UserToAdmins.user_id)).all()
        mail = UserToAdmins.query.filter_by().order_by(UserToAdmins.id.asc()).all()
        return render_template('admin/index.html',params=params,post_cnt=post_cnt,cat_cnt=cat_cnt,auth_cnt=auth_cnt,bugreport_cnt=bugreport_cnt,user=user,mail=mail,mail_senders=mail_senders)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)
        #return redirect(url_for('admin_login'))


@app.route('/admin/profile')
def admin_profile():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        aut_id = Authors.query.filter_by(username=username).first()
        if( not aut_id):
            no_of_posts = 0
        else:
            no_of_posts = Blogpost.query.filter_by(user_id=aut_id.id).count()
        posts = Blogpost.query.filter_by(user_id=aut_id.id).order_by(Blogpost.id.desc()).all()
        return render_template('admin/pages/posts/profile.html',params=params,user=user,no_of_posts=no_of_posts,posts=posts) 
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/profile-edit', methods = ['GET', 'POST'])
def admin_profile_edit():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == 'POST':
            name = request.form.get('name')
            usernames = request.form.get('username')
            email =user.email
            f = request.files['myfile']
            user_existing = Authors.query.filter_by(username=usernames).first()
            user_admin = Admin.query.filter_by(email=email).first()
            user_author = Authors.query.filter_by(email=email).first()
            if(not user_existing):
                session['admin_username'] = usernames
                user_admin.name = name
                user_admin.username = usernames
                db.session.commit()
                user_author.name = name
                user_author.username = usernames
                db.session.commit()
                if f :
                    f.filename = secrets.token_hex(13) + ".png"
                    f.save(os.path.join(app.config['ADMINDP_UPLOAD_FOLDER'],secure_filename(f.filename)))
                    user_admin.profile = f.filename
                    db.session.commit()
                    user_author.profile = f.filename
                    db.session.commit()
                flash('Profile updated successfully','success')
                return redirect(url_for('admin_profile_edit'))
            else:
                if(user_existing.username==user.username):
                    user_admin.name = name
                    db.session.commit()
                    user_author.name = name
                    db.session.commit()
                    if f :
                        f.filename = secrets.token_hex(13) + ".png"
                        f.save(os.path.join(app.config['ADMINDP_UPLOAD_FOLDER'],secure_filename(f.filename)))
                        user_admin.profile = f.filename
                        db.session.commit()
                        user_author.profile = f.filename
                        db.session.commit()
                    flash('Profile updated successfully','success')
                    return redirect(url_for('admin_profile_edit'))
                else:
                    flash('Username exists, please select another!','warning')
                    return redirect(url_for('admin_profile_edit'))
        return render_template('/admin/pages/posts/profile-edit.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/dark-mode',methods=['GET','POST'])
def admin_dark_mode():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == 'POST':
            dark_mode_var = request.form.get('verification')
            if(dark_mode_var=="on"):
                dark_mode_var = 1
            else:
                dark_mode_var = 0
            if(user.darkmode == dark_mode_var):
                flash('Your changes has not affected your dashboard as you have saved the previous settings.','warning')
                return redirect(url_for('admin_dark_mode'))
            else:
                if(dark_mode_var == 1):
                    val = True
                    flash('Dark-mode has been activated successfully!','success')
                else:
                    val = False
                    flash('Dark-mode has been deactivated successfully!','success')
                user.darkmode = val
                db.session.commit()
        return render_template('/admin/pages/posts/darkmode.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/two-step-verification', methods=['GET', 'POST'])
def admin_two_step():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        aut_id = Authors.query.filter_by(username=username).first()
        if( not aut_id):
            no_of_posts = 0
        else:
            no_of_posts = Blogpost.query.filter_by(user_id=aut_id.id).count()
        if request.method == 'POST':
            two_step_var = request.form.get('verification')
            if(two_step_var=="on"):
                two_step_var = 1
            else:
                two_step_var = 0
            if(user.twostep == two_step_var):
                flash('Your changes has not affected your account as you have saved the previous settings.','warning')
                return redirect(url_for('admin_two_step'))
            else:
                if(two_step_var == 1):
                    val = True
                else:
                    val = False
                user.twostep = val
                db.session.commit()
                #myVar.tsv_otp = secrets.token_hex(5)
                #admin_tsv_otp(user.email)
                flash('Your two-step verification settings has been changed successfully!','success')
                admin_tsv_activated(user.email)
                return redirect(url_for('admin_two_step'))
        return render_template('/admin/pages/posts/two-step.html',params=params,user=user,no_of_posts=no_of_posts)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/two-step-verification-otp', methods=['GET', 'POST'])
def admin_twostep_otp():
    if('admin_username' not in session and 'admin_email' not in session):
        if request.method == 'POST':
            otp = request.form.get('otp')
            if(myVar.tsv_otp!=otp):
                flash('The OTP you have entered is incorrect!','danger')
                return redirect(url_for('admin_twostep_otp'))
            if (myVar.tsv_otp==otp):
                user = Admin.query.filter_by(email=myVar.myemail).first()
                myVar.tsv_otp = None
                myVar.myemail = None
                session.permanent = True
                session['admin_username'] = user.username
                session['admin_email'] = user.email
                if user.activate is False:
                    return redirect(url_for('admin_unconfirmed'))
                flash('You are now logged in to the dashboard!','success')
                return redirect(url_for('admin_dash'))
        return render_template('/admin/twostep-otp.html',params=params)
    if('admin_username'  in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))


@app.route('/admin/change-password', methods = ['GET', 'POST'])
def admin_change_password():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == 'POST':
            present_pass = request.form.get('present_pass')
            new_pass = request.form.get('new_pass')
            conf_new_pass = request.form.get('conf_new_pass')
            is_pass = bcrypt.check_password_hash(user.password,present_pass)
            if (not is_pass):
                flash('You have entered wrong Password. Check and try again!','danger')
                return redirect(url_for('admin_change_password'))
            if (new_pass != conf_new_pass):
                flash('Your new Passwords do not match.','warning')
                return redirect(url_for('admin_change_password'))
            if (present_pass == new_pass):
                flash('Present password and new password cannot be the same!','warning')
                return redirect(url_for('admin_change_password'))
            user.password = bcrypt.generate_password_hash(new_pass)
            db.session.commit()
            pwd_email = user.email
            admin_changed_pwd(pwd_email)
            flash('Your Password has been successfully changed!','success')
            return redirect(url_for('admin_profile'))
    
        return render_template('/admin/pages/posts/change-password.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/all-categories')
def admin_all_categories():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        categories = Category.query.filter_by().all()
        return render_template('admin/pages/posts/allcategories.html',params=params,categories=categories,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/manage-category/<int:id>', methods=['GET','POST'])
def admin_manage_category(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        cat = Category.query.filter_by(id=id).first()
        if(not cat):
            flash('Category does not exist!','warning')
            return redirect('/admin/all-categories')
        return render_template('admin/pages/posts/managecategory.html',params=params,cat=cat,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/delete-category/<int:id>')
def admin_delete_category(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        presentpost = Blogpost.query.filter_by(category_id=id).all()
        cat = Category.query.filter_by(id=id).first()
        if(not cat):
            flash('Category does not exist!','warning')
            return redirect('/admin/all-categories')
        if(not presentpost):
            db.session.delete(cat)
            db.session.commit()
            #updatecat(id)
            flash('Category Deleted successfully!','success')
        else:
            flash('Cannot delete category as it has some posts associated with it!','danger')
        return redirect('/admin/all-categories')
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route("/admin/edit-category/<string:id>", methods = ['GET', 'POST'])
def admin_edit_category(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        cat = Category.query.filter_by(id=id).first()
        if(not cat):
            flash('Category does not exist!','warning')
            return redirect('/admin/all-categories')
        if request.method == 'POST':
            box_cat = request.form.get('catname')
            cat = Category.query.filter_by(id=id).first()
            cat.name = box_cat
            db.session.commit()
            flash('Your category has been successfully edited!','success')
            return redirect('/admin/edit-category/'+id)
        cat = Category.query.filter_by(id=id).first()
        return render_template('admin/pages/posts/editcategory.html', params=params, cat=cat,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/add-category', methods = ['GET', 'POST'])
def admin_add_category():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method=="POST":
            presentcat = Category.query.filter_by(name=request.form.get('catname')).first()
            if(presentcat):
                flash("The category name already exists!",'danger')
                return redirect(url_for('admin_add_category'))
            cat = request.form.get("catname")
            enter_cat = Category(name=cat)
            db.session.add(enter_cat)
            db.session.commit()
            flash('Your category has been successfully created!','success')
            return redirect(url_for('admin_all_categories'))
        return render_template('admin/pages/posts/addcategory.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/upload-image')
def admin_upload_image():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        hists = os.listdir('website/static/images/uploads')
        filen = [file for file in hists]
        hists = ['images/uploads/' + file for file in hists]
        return render_template('admin/pages/posts/uploadimage.html',params=params,hists = hists,filen=filen,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/uploader',methods = ['GET', 'POST'])
def admin_uploader():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == "POST":
            f = request.files['myfile']
            if f.filename == '':
                flash('Choose an image to Upload!','warning')
                return redirect(url_for('admin_upload_image'))
            if f :
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                flash('Uploaded Successfully!','success')
                return redirect(url_for('admin_upload_image'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)
        
@app.route('/admin/remover/<string:fname>',methods = ['GET','POST'])
def admin_remover(fname):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        hists = os.listdir('website/static/images/uploads')
        hists = ['images/uploads/' + fname]
        paths = app.config['UPLOAD_FOLDER'] + "\\" + fname
        if (request.method == "POST") and (os.path.isfile(paths)):
            filename = fname 
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(filename)))
            flash('Image Deleted Successfully!','success')
            return redirect(url_for('admin_upload_image'))
        flash('Image does not exists!','warning')
        return redirect(url_for('admin_upload_image'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/image-details/<string:img>',methods = ['GET', 'POST'])
def admin_image_detail(img):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        hists = os.listdir('website/static/images/uploads')
        hists = ['images/uploads/' + img]
        paths = app.config['UPLOAD_FOLDER'] + "\\" + img
        if os.path.isfile(paths):
            im = cv2.imread(paths)
            h, w, c = im.shape
            return render_template('/admin/pages/posts/imagedetails.html',params=params,h=h,w=w,hists=hists,img=img,user=user)
        flash('Image does not exists!','warning')
        return redirect(url_for('admin_upload_image'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/bug-report/<int:id>')
def admin_bug_reports(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bug = Bugreport.query.filter_by(id=id).first()
        if(not bug):
            flash('The Bug does not exists!','warning')
            return redirect('/admin/all-bug-reports')
        return render_template('/admin/pages/bugreport.html',params=params,bug=bug,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/print-bug-report/<int:id>')
def admin_print_bug_report(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bug = Bugreport.query.filter_by(id=id).first()
        if(not bug):
            flash('The Bug does not exists!','warning')
            return redirect('/admin/all-bug-reports')
        return render_template('/admin/pages/bugreport-print.html',params=params,bug=bug,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/bug-resolved/<int:id>',methods = ['GET', 'POST'])
def admin_bug_resolved(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bug = Bugreport.query.filter_by(id=id).first()
        if(not bug):
            flash('The Bug does not exists!','warning')
            return redirect('/admin/all-bug-reports')
        if (request.method == "POST"):
            bug = Bugreport.query.filter_by(id=id).first()
            bug.status = 1
            db.session.commit()
            flash('Bug status changed to resolved!','success')
            return redirect(url_for('admin_all_bug_reports'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/bug-unresolved/<int:id>',methods = ['GET', 'POST'])
def admin_bug_unresolved(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bug = Bugreport.query.filter_by(id=id).first()
        if(not bug):
            flash('The Bug does not exists!','warning')
            return redirect('/admin/all-bug-reports')
        if (request.method == "POST"):
            bug = Bugreport.query.filter_by(id=id).first()
            bug.status = 0
            db.session.commit()
            flash('Bug status changed to unresolved!','success')
            return redirect(url_for('admin_all_bug_reports'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/delete-bug-report/<int:id>',methods = ['GET', 'POST'])
def admin_delete_bug_report(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bug = Bugreport.query.filter_by(id=id).first()
        if(not bug):
            flash('The Bug does not exists!','warning')
            return redirect('/admin/all-bug-reports')
        if (request.method == "POST"):
            filename = bug.scrnshot
            os.remove(os.path.join(app.config['UPLOADED_PHOTOS_DEST'],secure_filename(filename)))
            db.session.delete(bug)
            db.session.commit()
            #updatebug(id)
            flash('Bug Report has been deleted successfully!','success')
            return redirect(url_for('admin_all_bug_reports'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)
        
@app.route('/admin/all-bug-reports')
def admin_all_bug_reports():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        bugs = Bugreport.query.filter_by().all()
        unresolved = Bugreport.query.filter_by(status=0).all()
        resolved = Bugreport.query.filter_by(status=1).all()
        return render_template('/admin/pages/all-bugreports.html',params=params,bugs=bugs,unresolved=unresolved,resolved=resolved,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/contact-list')
def admin_contact_list():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        contact = Contact.query.filter_by().all()
        return render_template('/admin/pages/contact.html',contact=contact,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/admin-registration-code')
def admin_registration_code():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        code = Admincode.query.filter_by().all()
        return render_template('admin/pages/registration-code.html',params=params,code=code,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/edit-admin-registration-code',methods=['GET','POST'])
def edit_admin_registration_code():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        code = Admincode.query.filter_by(id=1).first()
        if request.method == 'POST':
            box_code = request.form.get('codename')
            code.code = box_code
            code.date = datetime.now()
            db.session.commit()
            flash('Admin registration code has been successfully edited!','success')
            return redirect('/admin/edit-admin-registration-code')
        return render_template('/admin/pages/edit-registration-code.html',params=params,code=code,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/all-posts')
def admin_all_posts():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        the_user = Authors.query.filter_by(username=username).first()
        posts = Posts.query.filter_by(fair_id=None).filter_by(user_id=the_user.id).all()
        published = Blogpost.query.filter_by(user_id=the_user.id).all()
        categories = Category.query.filter_by().all()
        return render_template('admin/pages/posts/allposts.html',params=params,posts=posts,categories=categories,user=user,published=published)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/add-post',methods = ['GET', 'POST'])
def admin_add_post():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        categories = Category.query.filter_by().all()
        if request.method == "POST":
            title = request.form.get('posttitle')
            slug = request.form.get('postslug')
            draft_title = Posts.query.filter_by(title=title).first()
            published_title = Blogpost.query.filter_by(title=title).first()
            draft_slug = Posts.query.filter_by(slug=slug).first()
            published_slug = Blogpost.query.filter_by(slug=slug).first()
            if(draft_slug or published_slug):
                flash('Change the slug, this slug exists!','warning')
                return redirect(url_for('admin_add_post'))
            if(draft_title or published_title):
                flash('Change the title, this title exists!','warning')
                return redirect(url_for('admin_add_post'))
            body = request.form.get('postbody')
            cat = request.form.get('postcategory')
            cat_id = Category.query.filter_by(name=cat).first()
            f = request.files['myfile']
            if f.filename == '':
                flash('Choose an image to Upload!','warning')
                return redirect(url_for('admin_add_post'))
            if f :
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            the_user = Authors.query.filter_by(username=username).first()
            entry = Posts(title=title,slug=slug,body=body,category_id=cat_id.id,image=f.filename,user_id=the_user.id,date_pub=datetime.now(),draft=True)
            db.session.add(entry)
            db.session.commit()
            flash('Your Post has been successfully added!','success')
            return redirect(url_for('admin_all_posts'))
        return render_template('admin/pages/posts/addpost.html',params=params,user=user,categories=categories)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/manage-post/<id>')
def admin_manage_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Posts.query.filter_by(id=id).first()
        categories = Category.query.filter_by().all()
        the_user = Authors.query.filter_by(username=username).first()
        if (not posts):
            flash('Post does not exist!','warning')
            return redirect(url_for('admin_all_posts'))
        if(the_user.id!=posts.user_id):
            flash('This post does not belongs to you!','danger')
            return redirect(url_for('admin_all_posts'))
        if(posts.draft==0):
            flash('Post is not available for editing!','warning')
            return redirect(url_for('admin_all_posts'))
        if(the_user.id==posts.user_id):
            return render_template('admin/pages/posts/managepost.html',params=params,user=user,categories=categories,posts=posts)
        else:
            flash('This post does not belongs to you.','danger')
            return redirect(url_for('admin_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/publish-request/<id>',methods=['POST'])
def admin_publish_request(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == "POST":
            the_posts = Posts.query.filter_by(id=id).first()
            the_posts.draft = False
            db.session.commit()
            flash('Your post has been sent for a review before publishing!','success')
            return redirect(url_for('admin_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/update-post/<id>',methods=['POST'])
def admin_update_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == "POST":
            title = request.form.get('posttitle')
            slug = request.form.get('postslug')
            the_posts = Posts.query.filter_by(id=id).first()
            draft_slug = Posts.query.filter_by(slug=slug).first()
            published_slug = Blogpost.query.filter_by(slug=slug).first()
            draft_title = Posts.query.filter_by(title=title).first()
            published_title = Blogpost.query.filter_by(title=title).first()
            if(draft_slug or published_slug):
                if(draft_slug.id!=the_posts.id):
                    flash('Change the slug, this slug exists!','warning')
                    return redirect(url_for('admin_manage_post',id=id))
            if(draft_title or published_title):
                if(draft_title.id!=the_posts.id):
                    flash('Change the title, this title exists!','warning')
                    return redirect(url_for('admin_manage_post',id=id))
            the_posts.slug = slug
            body = request.form.get('postbody')
            cat = request.form.get('postcategory')
            f = request.files['myfile']
            if f.filename != '' and f:
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                the_posts.image = f.filename
            the_posts.title = title
            the_posts.body = body
            if cat:
                cat_id = Category.query.filter_by(name=cat).first()
                the_posts.category_id = cat_id.id
            db.session.commit()
            flash('The Post has been Updated successfully!','success')
            return redirect(url_for('admin_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)
    
@app.route('/admin/manage-user-posts')
def admin_manage_user_posts():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Posts.query.filter_by(fair_id=None).filter_by(draft=False).all()
        published = Posts.query.filter_by(fair_id=not None).filter_by(status=1).filter_by(draft=False).all()
        categories = Category.query.filter_by().all()
        the_author = Authors.query.filter_by().all()
        return render_template('admin/pages/posts/manage_user_posts.html',params=params,posts=posts,categories=categories,user=user,published=published,the_author=the_author)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/post-actions/<id>',methods=['GET','POST'])
def admin_post_actions(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Posts.query.filter_by(id=id).first()
        categories = Category.query.filter_by().all()
        if (not posts):
            flash('Post does not exist!','warning')
            return redirect(url_for('user_all_posts'))
        if(posts.draft==1):
            flash('Post is not available for managing!','warning')
            return redirect(url_for('user_all_posts'))
        the_user = Authors.query.filter_by(id=posts.user_id).first()
        return render_template('admin/pages/posts/post-actions.html',params=params,user=user,categories=categories,posts=posts,the_user=the_user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/update-user-post/<id>',methods=['POST'])
def update_user_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == "POST":
            title = request.form.get('posttitle')
            slug = request.form.get('postslug')
            the_posts = Posts.query.filter_by(id=id).first()
            draft_slug = Posts.query.filter_by(slug=slug).first()
            published_slug = Blogpost.query.filter_by(slug=slug).first()
            draft_title = Posts.query.filter_by(title=title).first()
            published_title = Blogpost.query.filter_by(title=title).first()
            if(draft_slug or published_slug):
                if(draft_slug.id!=the_posts.id):
                    flash('Change the slug, this slug exists!','warning')
                    return redirect(url_for('admin_post_actions',id=id))
            if(draft_title or published_title):
                if(draft_title.id!=the_posts.id):
                    flash('Change the title, this title exists!','warning')
                    return redirect(url_for('admin_post_actions',id=id))
            body = request.form.get('postbody')
            cat = request.form.get('postcategory')
            f = request.files['myfile']
            if f.filename != '' and f:
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                the_posts.image = f.filename
            the_posts.title = title
            the_posts.slug = slug
            the_posts.body = body
            if cat:
                cat_id = Category.query.filter_by(name=cat).first()
                the_posts.category_id = cat_id.id
            db.session.commit()
            flash('The Post has been Updated successfully!','success')
            return redirect(url_for('admin_manage_user_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/reject-post/<id>',methods=['POST'])
def reject_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Posts.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not posts or posts.draft==1):
                flash('Post does not exist!','warning')
                return redirect(url_for('admin_manage_user_posts'))
            posts.draft = 1
            posts.status = 0
            db.session.commit()
            flash('Post has been rejected!','warning')
            return redirect(url_for('admin_manage_user_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/publish-post/<id>', methods = ['POST'])
def publish_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Posts.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not posts or posts.draft==1):
                flash('Post does not exist!','warning')
                return redirect(url_for('admin_manage_user_posts'))
            entry = Blogpost(title=posts.title,slug=posts.slug,body=posts.body,category_id=posts.category_id,image=posts.image,user_id=posts.user_id,views=0,date_pub=datetime.now(),rough_id=posts.id)
            db.session.add(entry)
            db.session.commit()
            posts.draft = 0
            posts.status = 1
            db.session.commit()
            post_var = Blogpost.query.filter_by(slug=posts.slug).first()
            posts.fair_id = post_var.id
            db.session.commit()
            flash('Post has been published successfully!','success')
            return redirect(url_for('admin_manage_user_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/delete-published-post/<id>', methods = ['POST'])
def delete_published_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Blogpost.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not posts):
                flash('Post does not exist!','warning')
                return redirect(url_for('published_post'))
            draft_post = Posts.query.filter_by(fair_id=posts.id).first()
            db.session.delete(posts)
            db.session.commit()
            db.session.delete(draft_post)
            db.session.commit()
            flash('The post was deleted successfully','success')
            return redirect(url_for('published_post'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/published-posts')
def published_post():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        published = Blogpost.query.all()
        authors = Authors.query.all()
        return render_template('admin/pages/posts/published.html',params=params,user=user,published=published,authors=authors)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/manage-published-post/<id>')
def manage_published_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Blogpost.query.filter_by(id=id).first()
        authors = Authors.query.all()
        categories = Category.query.filter_by().all()
        if (not posts):
            flash('Post does not exist!','warning')
            return redirect(url_for('published_post'))
        the_user = Authors.query.filter_by(id=posts.user_id).first()
        return render_template('admin/pages/posts/manage_published_post.html',params=params,user=user,posts=posts,authors=authors,the_user=the_user,categories=categories)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/revert-to-draft/<id>', methods = ['POST'])
def revert_to_draft(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        posts = Blogpost.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not posts):
                flash('Post does not exist!','warning')
                return redirect(url_for('published_post'))
            draft_post = Posts.query.filter_by(fair_id=posts.id).first()
            db.session.delete(posts)
            db.session.commit()
            draft_post.draft = True
            draft_post.status = None
            draft_post.fair_id = None
            db.session.commit()
            flash('The post was reverted to draft successfully','success')
            return redirect(url_for('published_post'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/update-published-post/<id>',methods=['POST'])
def update_published_post(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == "POST":
            title = request.form.get('posttitle')
            slug = request.form.get('postslug')
            a = Blogpost.query.filter_by(id=id).first()
            the_posts = Posts.query.filter_by(id=a.rough_id).first()
            draft_slug = Posts.query.filter_by(slug=slug).first()
            published_slug = Blogpost.query.filter_by(slug=slug).first()
            draft_title = Posts.query.filter_by(title=title).first()
            published_title = Blogpost.query.filter_by(title=title).first()
            if(draft_slug or published_slug):
                if(published_slug.rough_id!=the_posts.id):
                    flash('Change the slug, this slug exists!','warning')
                    return redirect(url_for('manage_published_post',id=id))
            if(draft_title or published_title):
                if(published_slug.rough_id!=the_posts.id):
                    flash('Change the title, this title exists!','warning')
                    return redirect(url_for('manage_published_post',id=id))
            body = request.form.get('postbody')
            cat = request.form.get('postcategory')
            published_blog_post = Blogpost.query.filter_by(rough_id=the_posts.id).first()
            f = request.files['myfile']
            if f.filename != '' and f:
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
                the_posts.image = f.filename
                published_blog_post.image = f.filename
            the_posts.title = title
            published_blog_post.title = title
            the_posts.slug = slug
            published_blog_post.slug = slug
            the_posts.body = body
            published_blog_post.body = body
            if cat:
                cat_id = Category.query.filter_by(name=cat).first()
                the_posts.category_id = cat_id.id
                published_blog_post.category_id = cat_id.id
            db.session.commit()
            db.session.commit()
            flash('The Post has been Updated successfully!','success')
            return redirect(url_for('published_post'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/mail/inbox')
def admin_mail_inbox():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        mail = UserToAdmins.query.filter_by().order_by(UserToAdmins.id.desc()).all()
        mail_senders = User.query.join(UserToAdmins,(User.id == UserToAdmins.user_id)).all()
        mail_unread = UserToAdmins.query.filter_by().filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()
        
        
        inbox_mail = AdminToAllUsers.query.filter_by().order_by(AdminToAllUsers.id.desc()).all()
        admin_mail_senders = Admin.query.join(AdminToUser,(Admin.id == AdminToUser.admin_id)).all()
        admin_mail = AdminToUser.query.filter_by(user_id=user.id).order_by(AdminToUser.id.desc()).all()
        
        return render_template('admin/pages/mailbox/mailbox.html',params=params,user=user,mail=mail,mail_unread=mail_unread,inbox_mail=inbox_mail,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread,admin_mail=admin_mail,admin_mail_senders=admin_mail_senders)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/mail/read/<id>')
def admin_mail_read(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        mail = UserToAdmins.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exists!','warning')
            return redirect('/admin/mail/compose')
        mail_senders = User.query.join(UserToAdmins,(User.id == UserToAdmins.user_id)).all()
        mail_unread = UserToAdmins.query.filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()
        mail.read = True
        db.session.commit()
        return render_template('admin/pages/mailbox/user-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread,mail_senders=mail_senders)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/mail/admin-mail/<id>')
def admin_mail_admin_mail(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        mail = AdminToAllUsers.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exist!','warning')
            return redirect('/admin/mail/compose')
        
        mail_senders = Admin.query.join(AdminToAllUsers,(Admin.id == AdminToAllUsers.admin_id)).all()
        mail_unread = UserToAdmins.query.filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()
        return render_template('admin/pages/mailbox/read-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/mail/user-admin-mail/<id>')
def admin_mail_user_admin_mail(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        mail = AdminToUser.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exists!','warning')
            return redirect('/admin/mail/compose')
        mail_senders = Admin.query.join(AdminToUser,(Admin.id == AdminToUser.admin_id)).all()
        mail_unread = UserToAdmins.query.filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()
        return render_template('admin/pages/mailbox/read-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/user-mail-delete/<id>',methods=['GET','POST'])
def admin_user_mail_delete(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        mail = UserToAdmins.query.filter_by(id=id).first()
        if request.method == 'POST':
            db.session.delete(mail)
            db.session.commit()
            flash('The mail from user has been successfully deleted!','success')
            return redirect(url_for('admin_mail_inbox'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/mail/sent')
def admin_mail_sent():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        sent_all_mail = AdminToAllUsers.query.filter_by(admin_id=user.id).order_by(AdminToAllUsers.id.desc()).all()
        mail_senders = Admin.query.join(AdminToAllUsers,(Admin.id == AdminToAllUsers.admin_id)).all()
        mail_to = User.query.join(AdminToUser,(User.id == AdminToUser.user_id)).all()
        sent_mail = AdminToUser.query.filter_by(admin_id=user.id).order_by(AdminToUser.id.desc()).all()
        
        mail = UserToAdmins.query.filter_by(user_id=user.id).order_by(UserToAdmins.id.desc()).all()
        mail_unread = UserToAdmins.query.filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()
        
        return render_template('admin/pages/mailbox/mailsent.html',params=params,user=user,mail=mail,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread,sent_all_mail=sent_all_mail,mail_senders=mail_senders,sent_mail=sent_mail,mail_to=mail_to)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/mail/compose', methods = ['GET', 'POST'])
def admin_mail_compose():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method == 'POST':
            sendto = request.form.get('sendto')
            subject = request.form.get('subject')
            message = request.form.get('message')
            if(sendto == "All Users"):
                entry = AdminToAllUsers(admin_id=user.id,subject=subject,message=message,date=datetime.now())
                db.session.add(entry)
                db.session.commit()
                flash('Your mail was sent to all Users!','success')
                return redirect(url_for('admin_mail_sent'))
            else:
                sendtouser = User.query.filter_by(username=sendto).first()
                entry = AdminToUser(admin_id=user.id,user_id=sendtouser.id,subject=subject,message=message,date=datetime.now(),read=False)
                db.session.add(entry)
                db.session.commit()
                flash('Your mail was sent successfully to the user!','success')
                return redirect(url_for('admin_mail_sent'))
        usertable = User.query.filter_by().all()
        mail_unread = UserToAdmins.query.filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(admin_id=user.id).filter_by(read=False).count()

        return render_template('admin/pages/mailbox/compose.html',params=params,user=user,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread,usertable=usertable)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/api', methods = ['GET', 'POST'])
def admin_api():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        return render_template('admin/pages/api.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/change-api',methods=['POST'])
@limiter.limit("2/7days")
def admin_change_api():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        if request.method =="POST":
            user.apikey=secrets.token_hex(17)
            db.session.commit()
            flash('Your API Key has been changed successfully!','success')
            return redirect(url_for('admin_api'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/all-admins')
def all_admins():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        admin_list = Admin.query.filter_by().all()

        return render_template('admin/pages/all_admins.html',params=params,user=user,admin_list=admin_list)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/all-users')
def all_users():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        user_list = User.query.filter_by().all()

        return render_template('admin/pages/all_users.html',params=params,user=user,user_list=user_list)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/admin/ban-user/<int:id>',methods=['POST'])
def ban_user(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        the_user = User.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not the_user):
                flash('The user does not exists!','danger')
                return redirect(url_for('all_users'))
            the_user.ban = True
            db.session.commit()
            flash('The user has been banned!','danger')
            return redirect(url_for('all_users'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/unban-user/<int:id>',methods=['POST'])
def unban_user(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        the_user = User.query.filter_by(id=id).first()
        if request.method == 'POST':
            if (not the_user):
                flash('The user does not exists!','danger')
                return redirect(url_for('all_users'))
            the_user.ban = False
            db.session.commit()
            flash('The user has been unbanned!','warning')
            return redirect(url_for('all_users'))
        
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/admin/add-user',methods=['GET','POST'])
def admin_add_user():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        rand_pass = secrets.token_hex(7)
        if request.method == "POST":
            name = request.form.get('name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            is_user = User.query.filter_by(username=username).first()
            admin_user = Admin.query.filter_by(username=username).first()
            is_email = User.query.filter_by(email=email).first()
            admin_email = Admin.query.filter_by(email=email).first()
            if(is_user or admin_user):
                flash("Username already exists!",'warning')
                return redirect(url_for('admin_add_user'))
            if(is_email or admin_email):
                flash("Email already exists!",'warning')
                return redirect(url_for('admin_add_user'))
            if check_email_validation(email):
                password_hash = bcrypt.generate_password_hash(password)
                api = secrets.token_hex(17)
                add_user = User(name=name,username=username,email=email,password=password_hash,profile='profile.jpg',date=datetime.now(),activate=True,twostep=False,darkmode=False,apikey=api,ban=False)
                db.session.add(add_user)
                db.session.commit()
                add_author = Authors(name=name,username=username,email=email,profile='profile.jpg',date=datetime.now())
                db.session.add(add_author)
                db.session.commit()
                admin_create_user(email,username,password)
                flash("User has been successfully created!",'success')
                return redirect(url_for('all_users'))
            flash("Email must end with .com!",'danger')
            return redirect(url_for('admin_add_user'))
        return render_template('admin/pages/add_user.html',params=params,user=user,rand_pass=rand_pass)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)


@app.route('/congratulations/<id>')
def admin_congratulations(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))
    if(str(myVar.uuid_url)==str(id) or str(myVar.resend_url)==str(id)) :
        return render_template('/admin/registration/verify-email.html',params=params)
    else :
        return redirect(url_for('admin_dash'))

@app.route('/unconfirmed')
def admin_unconfirmed():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            #return redirect(url_for('admin_unconfirmed'))
            return render_template('/admin/registration/unconfirmed.html',params=params,user=user)
        else :
            return redirect(url_for('admin_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('admin/admin-login.html',params=params)

@app.route('/verified/<id>')
def admin_verified(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))
    if(str(myVar.uuid_url)==str(id)) :
        return render_template('/admin/registration/email-verified.html',params=params)
    else :
        return redirect(url_for('admin_dash'))


@app.route('/email-not-valid/<id>')
def admin_email_not_valid(id):
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))
    if(str(myVar.uuid_url)==str(id)):
        return render_template('/admin/registration/mail-not-accepted.html',params=params)
    else :
        return redirect(url_for('admin_dash'))

@app.route('/token-expired')
def admin_token_expired():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        return redirect(url_for('admin_dash'))
    return render_template('/admin/registration/token-expired.html',params=params)

@app.route('/already-verified')
def admin_already_verified():
    if('admin_username' in session and 'admin_email' in session):
        username = session['admin_username']
        user = Admin.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('admin_unconfirmed'))
        else : 
            return redirect(url_for('admin_dash'))
    else:
        return render_template('/admin/registration/already-verified.html',params=params)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    # clear browser cache
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.context_processor
def context_processor():
    notification_bug_count = Bugreport.query.filter_by(status=0).count()
    notification_mail_unread = UserToAdmins.query.filter_by(read=0).count()
    return dict(notification_bug_count=notification_bug_count,notification_mail_unread=notification_mail_unread)