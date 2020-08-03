from website import app,db
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from flask_mail import Mail
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.sql import func
import math
import os
import os.path
import secrets
from .models import User
import json
from website.body.models import Blogpost,Category,Authors,Bugreport,Contact,UserToAdmins,AdminToAllUsers,AdminToUser,Posts
from website.admin.models import Admin,Admincode
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


with open('userconfig.json', 'r') as c:
    params = json.load(c)["params"]



app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config['USERDP_UPLOAD_FOLDER'] = params['userdp_upload_location']
bcrypt = Bcrypt(app)


#JSON auto alphabetical sorting disabled
app.config['JSON_SORT_KEYS'] = False


#after 3 days the session will be logged out automatically
app.permanent_session_lifetime = timedelta(days=3)



class User_mailstore():
    myemail = None
    otp = None
    pwd = None
    uuid_url = None
    resend_url = None
    tsv_otp = None
    
userVar = User_mailstore()


def user_generate_confirmation_token(email, username):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    print('serializer',serializer)
    return serializer.dumps({'email': email, 'username': username}, salt=SALT)


def user_confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        result = serializer.loads(token, salt=SALT, max_age=expiration)
    except:
        return False
    return result


def user_check_email_validation(email):
    print('email', email)
    result = email.endswith('.com')
    return result


def user_send_mail(email, template):
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


def user_send_confirmation_mail(email, username):
    token = user_generate_confirmation_token(email, username)
    confirm_url = url_for('user_confirm_email', token=token, _external=True)
    html = render_template('user/registration/activate.html', confirm_url=confirm_url)
    user_send_mail(email, html)
    return



@app.route('/confirm-user/<token>')
def user_confirm_email(token):
    try:
        data = user_confirm_token(token)
    except:
        return redirect(url_for('user_token_expired'))
    if(data==False):
        return redirect(url_for('user_token_expired'))
    user = User.query.filter_by(username=data['username']).first()
    if user:
        if (user.activate==False):
            user.activate=True
            db.session.add(user)
            db.session.commit()
            new_author = Authors(name=user.name,username=user.username,email=user.email,profile=user.profile,date=datetime.now())
            db.session.add(new_author)
            db.session.commit()
        else:
            return redirect(url_for('user_already_verified'))
    userVar.uuid_url = uuid.uuid4()
    return redirect(url_for('user_verified',id=userVar.uuid_url))


@app.route('/user/forgot-password', methods=['GET', 'POST'])
def user_forgot_password():
    if('user_username' not in session and 'user_email' not in session):
        if request.method =='POST':
            username = request.form.get('username')
            email = request.form.get('email')
            user = User.query.filter_by(username=username).first()
            if (not user):
                flash('Username does not exists','warning')
            elif(not user.email==email):
                flash('Email does not match with the username','danger')
            else:
                userVar.myemail = email
                userVar.otp = secrets.token_hex(10)
                user_pwd_reset_mail(email)
                flash('OTP has been sent in your e-mail!','success')
                return redirect(url_for('user_otp'))
        return render_template('/user/user-forgot-pass.html',params=params)
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))


@app.route('/user/otp', methods=['GET', 'POST'])
def user_otp():
    if('user_username' not in session and 'user_email' not in session):
        if request.method == 'POST':
            otp = request.form.get('otp')
            if(userVar.otp!=otp):
                flash('The OTP you have entered is incorrect!','warning')
                return redirect(url_for('user_otp'))
            if (userVar.otp==otp):
                user = User.query.filter_by(email=userVar.myemail).first()
                userVar.pwd = secrets.token_hex(7)
                new_pass = bcrypt.generate_password_hash(userVar.pwd)
                user.password = new_pass
                db.session.commit()
                user_new_pwd(userVar.myemail)
                userVar.otp = None
                userVar.myemail = None
                userVar.pwd = None
                flash('New password has been sent through mail.','success')
                return redirect(url_for('user_login'))
        return render_template('/user/pwd-reset-otp.html',params=params)
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))



def user_pwd_reset_mail(email):
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
        userVar.otp,
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

def user_new_pwd(email):
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
        userVar.pwd,
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


def user_changed_pwd(email):
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


def user_tsv_activated(email):
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

def user_tsv_otp(email):
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
        userVar.tsv_otp,
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


@app.route('/signup', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        check_user = Authors.query.filter_by(username=username).first()
        if check_user:
            flash("The username already exists!",'warning')
            return redirect(url_for('user_register'))
        check_email = Authors.query.filter_by(email=email).first()
        if check_email:
            flash("The email id already exists!",'warning')
            return redirect(url_for('user_register'))
        if password != re_password :
            flash("Password do not match please check and try again!",'danger') 
            return redirect(url_for('user_register'))
        if user_check_email_validation(email):
            password_hash = bcrypt.generate_password_hash(password)
            api = secrets.token_hex(17)
            new_user = User(name=fullname,username=username,email=email,password=password_hash,profile='profile.jpg',date=datetime.now(),activate=False,twostep=False,darkmode=False,apikey=api,ban=False)
            db.session.add(new_user)
            db.session.commit()
            userVar.uuid_url = uuid.uuid4()
            user_send_confirmation_mail(email, username)
            return redirect(url_for('user_congratulations',id=userVar.uuid_url))
        else:
            userVar.uuid_url = uuid.uuid4()
            return redirect(url_for('user_email_not_valid',id=userVar.uuid_url))
    return render_template('user/register.html',params=params)


@app.route('/resend')
def user_resend_confirmation():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if (user.activate is False):
            #return redirect(url_for('admin_unconfirmed'))
            user_send_confirmation_mail(session['user_email'], session['user_username'])
            del session['user_username']
            del session['user_email']
            userVar.resend_url = uuid.uuid4()
            return redirect(url_for('user_congratulations',id=userVar.resend_url))
        else:
            if user.ban is True:
                del session['user_username']
                del session['user_email']
                flash('You have been banned by Admin!','danger')
                return redirect(url_for('user_login'))
            return redirect(url_for('user_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)
    
@app.route('/resend-cancel')
def user_resend_confirmation_cancel():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if (user.activate is False):
            del session['user_username']
            del session['user_email']
            return redirect(url_for('user_register'))
        else:
            if user.ban is True:
                del session['user_username']
                del session['user_email']
                flash('You have been banned by Admin!','danger')
                return redirect(url_for('user_login'))
            return redirect(url_for('user_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if('user_username' in session and 'user_email' in session):
        return redirect(url_for('user_dash'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User does not exist!','danger')
            return redirect(url_for('user_login'))
        check_pass = bcrypt.check_password_hash(user.password,password)
        if not check_pass:
            flash('Password do not match, try again!','warning')
            return redirect(url_for('user_login'))
        if user.ban is True:
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if(user.twostep==0):
            session.permanent = True
            session['user_username'] = user.username
            session['user_email'] = user.email
            if user.activate is False:
                return redirect(url_for('user_unconfirmed'))
            flash('You are now logged in to the dashboard!','success')
            return redirect(url_for('user_dash'))
        else:
            userVar.myemail = user.email
            userVar.tsv_otp = secrets.token_hex(5)
            user_tsv_otp(user.email)
            return redirect(url_for('user_twostep_otp'))
    return render_template('user/login.html',params=params)


@app.route('/user/dashboard')
def user_dash():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        aut_id = Authors.query.filter_by(username=username).first()
        if( not aut_id):
            post_published = 0
            post_rejected = 0
            post_draft = 0
            no_of_posts = 0
        else:
            post_rejected = Posts.query.filter_by(user_id=aut_id.id).filter_by(status=0).count()
            post_published = Blogpost.query.filter_by(user_id=aut_id.id).count()
            post_draft = Posts.query.filter_by(user_id=aut_id.id).filter_by(draft=1).count()
            no_of_posts = Posts.query.filter_by(user_id=aut_id.id).count()
        mail_senders = Admin.query.join(AdminToUser,(Admin.id == AdminToUser.admin_id)).all()
        mail = AdminToUser.query.filter_by().order_by(AdminToUser.id.asc()).all()
        return render_template('user/index.html',params=params,post_published=post_published,user=user,mail_senders=mail_senders,mail=mail,post_rejected=post_rejected,post_draft=post_draft,no_of_posts=no_of_posts)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)
        #return redirect(url_for('admin_login'))


@app.route('/logout', methods=['GET','POST'])
def user_logout():
    if('user_username' in session and 'user_email' in session):
        del session['user_username']
        del session['user_email']
        return redirect(url_for('user_login'))
    else:
        return redirect(url_for('home'))


@app.route('/user/profile')
def user_profile():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        aut_id = Authors.query.filter_by(username=username).first()
        if( not aut_id):
            no_of_posts = 0
        else:
            no_of_posts = Blogpost.query.filter_by(user_id=aut_id.id).count()
        posts = Blogpost.query.filter_by(user_id=aut_id.id).order_by(Blogpost.id.desc()).all()
        return render_template('user/pages/posts/profile.html',params=params,user=user,no_of_posts=no_of_posts,posts=posts) 
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/profile-edit', methods = ['GET', 'POST'])
def user_profile_edit():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method == 'POST':
            name = request.form.get('name')
            usernames = request.form.get('username')
            email = user.email
            f = request.files['myfile']
            user_existing = Authors.query.filter_by(username=usernames).first()
            user_user = User.query.filter_by(email=email).first()
            user_author = Authors.query.filter_by(email=email).first()
            if(not user_existing):
                session['user_username'] = usernames
                user_user.name = name
                user_user.username = usernames
                db.session.commit()
            
                user_author.name = name
                user_author.username = usernames
                db.session.commit()
                if f :
                    f.filename = secrets.token_hex(13) + ".png"
                    f.save(os.path.join(app.config['USERDP_UPLOAD_FOLDER'],secure_filename(f.filename)))
                    user_user.profile = f.filename
                    db.session.commit()
                    user_author.profile = f.filename
                    db.session.commit()
                flash('Profile updated successfully','success')
                return redirect(url_for('user_profile_edit'))
            else:
                if(user_existing.username==user.username):
                    user_user.name = name
                    db.session.commit()
                    user_author.name = name
                    db.session.commit()
                    if f :
                        f.filename = secrets.token_hex(13) + ".png"
                        f.save(os.path.join(app.config['USERDP_UPLOAD_FOLDER'],secure_filename(f.filename)))
                        user_user.profile = f.filename
                        db.session.commit()
                        user_author.profile = f.filename
                        db.session.commit()
                    flash('Profile updated successfully','success')
                    return redirect(url_for('user_profile_edit'))
                else:
                    flash('Username exists, please select another!','warning')
                    return redirect(url_for('user_profile_edit'))
        return render_template('/user/pages/posts/profile-edit.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/dark-mode',methods=['GET','POST'])
def user_dark_mode():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method == 'POST':
            dark_mode_var = request.form.get('verification')
            if(dark_mode_var=="on"):
                dark_mode_var = 1
            else:
                dark_mode_var = 0
            if(user.darkmode == dark_mode_var):
                flash('Your changes has not affected your dashboard as you have saved the previous settings.','warning')
                return redirect(url_for('user_dark_mode'))
            else:
                if(dark_mode_var == 1):
                    val = True
                    flash('Dark-mode has been activated successfully!','success')
                else:
                    val = False
                    flash('Dark-mode has been deactivated successfully!','success')
                user.darkmode = val
                db.session.commit()
        return render_template('/user/pages/posts/darkmode.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/two-step-verification', methods=['GET', 'POST'])
def user_two_step():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
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
                return redirect(url_for('user_two_step'))
            else:
                if(two_step_var == 1):
                    val = True
                else:
                    val = False
                user.twostep = val
                db.session.commit()
                flash('Your two-step verification settings has been changed successfully!','success')
                user_tsv_activated(user.email)
                return redirect(url_for('user_two_step'))
        return render_template('/user/pages/posts/two-step.html',params=params,user=user,no_of_posts=no_of_posts)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/two-step-verification-otp', methods=['GET', 'POST'])
def user_twostep_otp():
    if('user_username' not in session and 'user_email' not in session):
        if request.method == 'POST':
            otp = request.form.get('otp')
            if(userVar.tsv_otp!=otp):
                flash('The OTP you have entered is incorrect!','danger')
                return redirect(url_for('user_twostep_otp'))
            if (userVar.tsv_otp==otp):
                user = User.query.filter_by(email=userVar.myemail).first()
                userVar.tsv_otp = None
                userVar.myemail = None
                session.permanent = True
                session['user_username'] = user.username
                session['user_email'] = user.email
                if user.activate is False:
                    return redirect(url_for('user_unconfirmed'))
                flash('You are now logged in to the dashboard!','success')
                return redirect(url_for('user_dash'))
        return render_template('/user/twostep-otp.html',params=params)
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if (user.activate is False):
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))

@app.route('/user/change-password', methods = ['GET', 'POST'])
def user_change_password():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method == 'POST':
            present_pass = request.form.get('present_pass')
            new_pass = request.form.get('new_pass')
            conf_new_pass = request.form.get('conf_new_pass')
            is_pass = bcrypt.check_password_hash(user.password,present_pass)
            if (not is_pass):
                flash('You have entered wrong Password. Check and try again!','warning')
                return redirect(url_for('user_change_password'))
            if (new_pass != conf_new_pass):
                flash('Your new Passwords do not match.','warning')
                return redirect(url_for('user_change_password'))
            if (present_pass == new_pass):
                flash('Present password and new password cannot be the same!','danger')
                return redirect(url_for('user_change_password'))
            user.password = bcrypt.generate_password_hash(new_pass)
            db.session.commit()
            pwd_email = user.email
            user_changed_pwd(pwd_email)
            flash('Your Password has been successfully changed!','success')
            return redirect(url_for('user_profile'))
    
        return render_template('/user/pages/posts/change-password.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/mail/compose', methods = ['GET', 'POST'])
def user_mail_compose():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method == 'POST':
            subject = request.form.get('subject')
            message = request.form.get('message')
            entry = UserToAdmins(user_id=user.id,subject=subject,message=message,date=datetime.now(),read=False)
            db.session.add(entry)
            db.session.commit()
            flash('Your mail was sent to the Admins!','success')
            return redirect(url_for('user_mail_sent'))
            
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        return render_template('user/pages/mailbox/compose.html',params=params,user=user,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/mail/sent')
def user_mail_sent():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        mail = UserToAdmins.query.filter_by(user_id=user.id).order_by(UserToAdmins.id.desc()).all()
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        return render_template('user/pages/mailbox/mailsent.html',params=params,user=user,mail=mail,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/mail/inbox')
def user_mail_inbox():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        mail_senders = Admin.query.join(AdminToAllUsers,(Admin.id == AdminToAllUsers.admin_id)).all()
        inbox_mail = AdminToAllUsers.query.filter_by().order_by(AdminToAllUsers.id.desc()).all()
        mail = UserToAdmins.query.filter_by(user_id=user.id).order_by(UserToAdmins.id.desc()).all()
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_senders = Admin.query.join(AdminToUser,(Admin.id == AdminToUser.admin_id)).all()
        admin_mail = AdminToUser.query.filter_by(user_id=user.id).order_by(AdminToUser.id.desc()).all()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        return render_template('user/pages/mailbox/mailbox.html',params=params,user=user,mail=mail,mail_unread=mail_unread,inbox_mail=inbox_mail,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread,admin_mail=admin_mail,admin_mail_senders=admin_mail_senders)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/mail/read/<id>')
def user_mail_read(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        mail = UserToAdmins.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exists!','warning')
            return redirect('/user/mail/compose')
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        if(mail.user_id==user.id):
            return render_template('user/pages/mailbox/read-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,admin_mail_unread=admin_mail_unread)
        else:
            flash('You do not have access to this mail.','danger')
            return redirect(url_for('user_mail_inbox'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/mail/admin-mail/<id>')
def user_mail_admin_mail(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        mail = AdminToAllUsers.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exists!','warning')
            return redirect('/user/mail/compose')
        mail_senders = Admin.query.join(AdminToAllUsers,(Admin.id == AdminToAllUsers.admin_id)).all()
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        return render_template('user/pages/mailbox/read-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/mail/admin-user-mail/<id>')
def user_mail_admin_user_mail(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        mail = AdminToUser.query.filter_by(id=id).first()
        if (not mail):
            flash('This mail does not exists!','warning')
            return redirect('/user/mail/compose')
        mail_unread = UserToAdmins.query.filter_by(user_id=user.id).filter_by(read=False).count()
        admin_mail_unread = AdminToUser.query.filter_by(user_id=user.id).filter_by(read=False).count()
        mail_senders = Admin.query.join(AdminToUser,(Admin.id == AdminToUser.admin_id)).all()
        if(mail.user_id==user.id):
            mail.read = True
            db.session.commit()
            return render_template('user/pages/mailbox/read-mail.html',params=params,user=user,mail=mail,mail_unread=mail_unread,mail_senders=mail_senders,admin_mail_unread=admin_mail_unread)
        else:
            flash('You do not have access to this mail.','danger')
            return redirect(url_for('user_mail_inbox'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/api', methods = ['GET', 'POST'])
def user_api():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return render_template('user/pages/api.html',params=params,user=user)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/change-api',methods=['POST'])
@limiter.limit("2/7days")
def user_change_api():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method =="POST":
            user.apikey=secrets.token_hex(17)
            db.session.commit()
            flash('Your API Key has been changed successfully!','success')
            return redirect(url_for('user_api'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Your API Key can be changed twice per week!",'danger')
    if('admin_username' in session and 'admin_email' in session):
        return redirect(url_for('admin_api'))
    elif('user_username' in session and 'user_email' in session):
        return redirect(url_for('user_api'))
    else:
        return "Too many requests to handle!"


@app.route('/user/add-post',methods = ['GET', 'POST'])
def user_add_post():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
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
                return redirect(url_for('user_add_post'))
            if(draft_title or published_title):
                flash('Change the title, this title exists!','warning')
                return redirect(url_for('user_add_post'))
            body = request.form.get('postbody')
            cat = request.form.get('postcategory')
            cat_id = Category.query.filter_by(name=cat).first()
            f = request.files['myfile']
            if f.filename == '':
                flash('Choose an image to Upload!','warning')
                return redirect(url_for('user_add_post'))
            if f :
                f.filename = secrets.token_hex(13) + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            the_user = Authors.query.filter_by(username=username).first()
            entry = Posts(title=title,slug=slug,body=body,category_id=cat_id.id,image=f.filename,user_id=the_user.id,date_pub=datetime.now(),draft=True)
            db.session.add(entry)
            db.session.commit()
            flash('Your Post has been successfully added!','success')
            return redirect(url_for('user_all_posts'))
        return render_template('user/pages/posts/addpost.html',params=params,user=user,categories=categories)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/all-posts')
def user_all_posts():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        the_user = Authors.query.filter_by(username=username).first()
        posts = Posts.query.filter_by(fair_id=None).filter_by(user_id=the_user.id).all()
        published = Blogpost.query.filter_by(user_id=the_user.id).all()
        categories = Category.query.filter_by().all()
        return render_template('user/pages/posts/allposts.html',params=params,user=user,posts=posts,categories=categories,published=published)
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/manage-post/<id>')
def user_manage_post(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        posts = Posts.query.filter_by(id=id).first()
        categories = Category.query.filter_by().all()
        the_user = Authors.query.filter_by(username=username).first()
        if (not posts):
            flash('Post does not exist!','warning')
            return redirect(url_for('user_all_posts'))
        if(the_user.id!=posts.user_id):
            flash('This post does not belongs to you!','danger')
            return redirect(url_for('user_all_posts'))
        if(posts.draft==0):
            flash('Post is not available for editing!','warning')
            return redirect(url_for('user_all_posts'))
        if(the_user.id==posts.user_id):
            return render_template('user/pages/posts/managepost.html',params=params,user=user,categories=categories,posts=posts)
        else:
            flash('This post does not belongs to you.','danger')
            return redirect(url_for('user_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user/update-post/<id>',methods=['POST'])
def user_update_post(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
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
                    return redirect(url_for('user_manage_post',id=id))
            if(draft_title or published_title):
                if(draft_title.id!=the_posts.id):
                    flash('Change the title, this title exists!','warning')
                    return redirect(url_for('user_manage_post',id=id))
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
            return redirect(url_for('user_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)


@app.route('/user/publish-request/<id>',methods=['POST'])
def user_publish_request(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        if request.method == "POST":
            the_posts = Posts.query.filter_by(id=id).first()
            the_posts.draft = False
            db.session.commit()
            flash('Your post has been sent for a review before publishing!','success')
            return redirect(url_for('user_all_posts'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user-congratulations/<id>')
def user_congratulations(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))
    if(str(userVar.uuid_url)==str(id) or str(userVar.resend_url)==str(id)) :
        return render_template('/user/registration/verify-email.html',params=params)
    else :
        return redirect(url_for('user_dash'))

@app.route('/user-unconfirmed')
def user_unconfirmed():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            #return redirect(url_for('admin_unconfirmed'))
            return render_template('/user/registration/unconfirmed.html',params=params,user=user)
        else :
            if user.ban is True:
                del session['user_username']
                del session['user_email']
                flash('You have been banned by Admin!','danger')
                return redirect(url_for('user_login'))
            return redirect(url_for('user_dash'))
    else:
        flash('Login to access Dashboard!','warning')
        return render_template('user/login.html',params=params)

@app.route('/user-verified/<id>')
def user_verified(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))
    if(str(userVar.uuid_url)==str(id)) :
        return render_template('/user/registration/email-verified.html',params=params)
    else :
        return redirect(url_for('user_dash'))


@app.route('/user-email-not-valid/<id>')
def user_email_not_valid(id):
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))
    if(str(userVar.uuid_url)==str(id)):
        return render_template('/user/registration/mail-not-accepted.html',params=params)
    else :
        return redirect(url_for('user_dash'))

@app.route('/user-token-expired')
def user_token_expired():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        if user.ban is True:
            del session['user_username']
            del session['user_email']
            flash('You have been banned by Admin!','danger')
            return redirect(url_for('user_login'))
        return redirect(url_for('user_dash'))
    return render_template('/user/registration/token-expired.html',params=params)

@app.route('/user-already-verified')
def user_already_verified():
    if('user_username' in session and 'user_email' in session):
        username = session['user_username']
        user = User.query.filter_by(username=username).first()
        if user.activate is False:
            return redirect(url_for('user_unconfirmed'))
        else :
            if user.ban is True:
                del session['user_username']
                del session['user_email']
                flash('You have been banned by Admin!','danger')
                return redirect(url_for('user_login'))
            return redirect(url_for('user_dash'))
    else:
        return render_template('/user/registration/already-verified.html',params=params)

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

@app.route('/api/v1.0/magnews')
def user_api_interface():
    key = request.args.get('key')
    if (not key):
        return jsonify({"error": "A valid API key is missing."}), 403
    a = Admin.query.filter_by(apikey=key).first()
    b = User.query.filter_by(apikey=key).first()
    if (a or b):
        output = []
        posts = Blogpost.query.filter_by().all()
        post_count = Blogpost.query.filter_by().count()
        for post in posts:
            post_data = {}
            post_data['id'] = post.id
            post_data['title'] = post.title
            post_data['slug'] = post.slug
            post_data['content'] = post.body
            cat = Category.query.filter_by(id=post.category.id).first()
            post_data['category'] = cat.name
            post_data['image'] = post.image
            aut = Authors.query.filter_by(id=post.user_id).first()
            post_data['author'] = aut.username
            post_data['views'] = post.views
            post_data['published_at'] = post.date_pub
            output.append(post_data)
        return jsonify({"blog_posts" : output, "count" : post_count})
    return jsonify({"error": "API key not valid."}), 403


@app.route('/api/v1.0/magnews/<int:id>')
def user_api_interface_by_id(id):
    key = request.args.get('key')
    if (not key):
        return jsonify({"error": "A valid API key is missing."}), 403
    a = Admin.query.filter_by(apikey=key).first()
    b = User.query.filter_by(apikey=key).first()
    if (a or b):
        output = []
        post = Blogpost.query.filter_by(id=id).first()
        if(post):
            post_data = {}
            post_data['id'] = post.id
            post_data['title'] = post.title
            post_data['slug'] = post.slug
            post_data['content'] = post.body
            cat = Category.query.filter_by(id=post.category.id).first()
            post_data['category'] = cat.name
            post_data['image'] = post.image
            aut = Authors.query.filter_by(id=post.user_id).first()
            post_data['author'] = aut.username
            post_data['views'] = post.views
            post_data['published_at'] = post.date_pub
            output.append(post_data)
            return jsonify({"blog_post" : output})
        else:
            return jsonify({"error": "Post does not exists."}), 403
    return jsonify({"error": "API key not valid."}), 403