from website import app,db,search,photos
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import math
from .models import Contact, Blogpost, Category, Authors, Bugreport
import json
import secrets


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)

@app.route('/')
def home():
    posts = Blogpost.query.order_by(Blogpost.id.desc()).all()
    
    writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
    return render_template('index.html',params=params, posts=posts,writers=writers)

@app.route('/blog')
def blog():
    
    writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
    posts = Blogpost.query.order_by(Blogpost.id.desc()).all()
    last = math.ceil(len(posts) / int(params['no_of_blog_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    if (int(params['no_of_blog_posts']) < len(posts)):
        posts = posts[(page - 1) * int(params['no_of_blog_posts']): (page - 1) * int(params['no_of_blog_posts']) + int(params['no_of_blog_posts'])]

        if (page == 1):
            prev = "#"
            next = "/blog?page=" + str(page + 1)
        elif(page == 2):
            prev = "/blog"
            next = "/blog?page=" + str(page + 1)
        elif (page == last):
            prev = "/blog?page=" + str(page - 1)
            next = "#"
        else:
            prev = "/blog?page=" + str(page - 1)
            next = "/blog?page=" + str(page + 1)
    else:
        prev = "#"
        next = "#"
    return render_template('blog.html', params=params, posts=posts, prev=prev, next=next ,writers=writers)

@app.route("/<string:post_slug>")
def blog_post(post_slug):
    posts = Blogpost.query.filter_by(slug=post_slug).first()
    if (not posts):
        
        writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
        return render_template("404.html",params=params,writers=writers)
    else :
        
        writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
        posts.views +=1
        db.session.commit()
    return render_template('blog-post.html', params=params, post=posts,writers=writers)

@app.route('/result')
def result():
    searchword = request.args.get('search')
    posts = Blogpost.query.msearch(searchword, fields=['title','body'])
    writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
    return render_template('result.html',posts=posts,searchword=searchword,writers=writers,params=params)

@app.route('/author/<string:authorname>')
def author_posts(authorname):
    autname = Authors.query.filter_by(username=authorname).first()
    if(not autname):
        return render_template("404.html",params=params)
    else:
        posts = Blogpost.query.filter_by(user_id=autname.id).order_by(Blogpost.id.desc()).all()
        writers = authorname
        last = math.ceil(len(posts) / int(params['no_of_author_posts']))
        page = request.args.get('page')
        if (not str(page).isnumeric()):
            page = 1
        page = int(page)
        if (int(params['no_of_author_posts']) < len(posts)):
            posts = posts[(page - 1) * int(params['no_of_author_posts']): (page - 1) * int(params['no_of_author_posts']) + int(params['no_of_author_posts'])]

            if (page == 1):
                prev = "#"
                next = "/author/"+authorname+"?page=" + str(page + 1)
            elif(page == 2):
                prev = "/author/"+authorname
                next = "/author/"+authorname+"?page=" + str(page+1)
            elif (page == last):
                prev = "/author/"+authorname+"?page=" + str(page - 1)
                next = "#"
            else:
                prev = "/author/"+authorname+"?page=" + str(page - 1)
                next = "/author/"+authorname+"?page=" + str(page + 1)
        else:
            prev = "#"
            next = "#"
            
    return render_template("authorpost.html",params=params,next=next,prev=prev,posts=posts,writers=writers)

@app.route('/category/<string:categoryname>')
def category_posts(categoryname):
    catname = Category.query.filter_by(name=categoryname).first()
    if(not catname):
        return render_template("404.html",params=params)
    else:
        posts = Blogpost.query.filter_by(category_id=catname.id).order_by(Blogpost.id.desc()).all()
        catname = categoryname
        writers = Authors.query.join(Blogpost,(Authors.id == Blogpost.user_id)).all()
        last = math.ceil(len(posts) / int(params['no_of_category_posts']))
        page = request.args.get('page')
        if (not str(page).isnumeric()):
            page = 1
        page = int(page)
        if (int(params['no_of_category_posts']) < len(posts)):
            posts = posts[(page - 1) * int(params['no_of_category_posts']): (page - 1) * int(params['no_of_category_posts']) + int(params['no_of_category_posts'])]

            if (page == 1):
                prev = "#"
                next = "/category/"+categoryname+"?page=" + str(page + 1)
            elif(page == 2):
                prev = "/category/"+categoryname
                next = "/category/"+categoryname+"?page=" + str(page+1)
            elif (page == last):
                prev = "/category/"+categoryname+"?page=" + str(page - 1)
                next = "#"
            else:
                prev = "/category/"+categoryname+"?page=" + str(page - 1)
                next = "/category/"+categoryname+"?page=" + str(page + 1)
        else:
            prev = "#"
            next = "#"
            
        
        
    return render_template("categorypost.html",params=params,catname=catname,next=next,prev=prev,posts=posts,writers=writers)

@app.route('/about')
def about():
    posts = Blogpost.query.filter_by().all()
    return render_template('about.html',params=params,posts=posts)

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    posts = Blogpost.query.filter_by().all()
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        website = request.form.get('website')
        message = request.form.get('message')
        entry = Contact(name=name,email=email,website=website,message=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        flash('Message sent successfully! We will reach you within 24 hours.','success')
        mail.send_message('New Message from Magnews Contact Form : ' + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\nEmail : " + email +"\nWebsite : " + website + "\nFrom : " + name
                          )
    return render_template('contact.html',params=params, posts=posts)

@app.route('/bug-report-form', methods=['GET','POST'])
def bugreport():
    if request.method == "POST":
        submitted_by = request.form.get('submittedby')
        email = request.form.get('email')
        title = request.form.get('bugtitle')
        bug_desc = request.form.get('bugdescription')
        bug_url = request.form.get('bugurl')
        platform = request.form.get('bugplatform')
        browser = request.form.get('bugbrowser')
        bug_date = request.form.get('bugdate')
        scrnshot = photos.save(request.files.get('scrnshot'), name=secrets.token_hex(13) + ".")
        expected_res = request.form.get('bugexpected')
        actual_res = request.form.get('bugactual')
        frequency = request.form.get('frequency')
        priority = request.form.get('priority')
        entry = Bugreport(sub_date=datetime.now(),submitted_by=submitted_by,email=email,title=title,bug_desc=bug_desc,bug_url=bug_url,platform=platform,browser=browser,bug_date=bug_date,scrnshot=scrnshot,expected_res=expected_res,actual_res=actual_res,frequency=frequency,priority=priority)
        db.session.add(entry)
        db.session.commit()
        flash('Thanks for reporting the Bug! We will catch it Soon!!','success')
        mail.send_message('New Message from Magnews Bug Report Form : ' + submitted_by,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body="Title : " + title + "\nDescription : " + bug_desc + "\nBug URL : " + bug_url + "\nPlatform : " + platform + "\nBrowser : " + browser +"\nBug Date(dd/mm/yyyy) : " + bug_date + "\nExpected Result : " + expected_res + "\nActual Result : " + actual_res + "\nFrequency : " + frequency + "\nPriority : " + priority + "\nEmail : " + email  + "\nFrom : " + submitted_by
                          )
        
    return render_template("body/bugreport.html",params=params)

@app.errorhandler(404)
def page_not_found(e):
    posts = Blogpost.query.filter_by().all()
    #app.logger.info(f"Page not found: {request.url}")
    return render_template("404.html",params=params, posts=posts), 404





@app.context_processor
def context_processor():
    categories = Category.query.join(Blogpost,(Category.id == Blogpost.category_id)).all()
    categorylist = Category.query.filter_by().order_by(Category.id.asc()).all()
    views = Blogpost.query.order_by(Blogpost.views.desc()).all()
    cat1 = Blogpost.query.filter_by(category_id=1).order_by(Blogpost.id.desc()).all()
    cat2 = Blogpost.query.filter_by(category_id=2).order_by(Blogpost.id.desc()).all()
    cat3 = Blogpost.query.filter_by(category_id=3).order_by(Blogpost.id.desc()).all()
    cat4 = Blogpost.query.filter_by(category_id=4).order_by(Blogpost.id.desc()).all()
    cat5 = Blogpost.query.filter_by(category_id=5).order_by(Blogpost.id.desc()).all()
    cat6 = Blogpost.query.filter_by(category_id=6).order_by(Blogpost.id.desc()).all()
    cat7 = Blogpost.query.filter_by(category_id=7).order_by(Blogpost.id.desc()).all()
    cat8 = Blogpost.query.filter_by(category_id=8).order_by(Blogpost.id.desc()).all()
    cat9 = Blogpost.query.filter_by(category_id=9).order_by(Blogpost.id.desc()).all()
    cat10 = Blogpost.query.filter_by(category_id=10).order_by(Blogpost.id.desc()).all()
    cat11 = Blogpost.query.filter_by(category_id=11).order_by(Blogpost.id.desc()).all()
    cat12 = Blogpost.query.filter_by(category_id=12).order_by(Blogpost.id.desc()).all()
    cat13 = Blogpost.query.filter_by(category_id=13).order_by(Blogpost.id.desc()).all()
    cat14 = Blogpost.query.filter_by(category_id=14).order_by(Blogpost.id.desc()).all()
    cat15 = Blogpost.query.filter_by(category_id=15).order_by(Blogpost.id.desc()).all()
    return dict(categories=categories,categorylist=categorylist, views=views, cat1=cat1,cat2=cat2,cat3=cat3,cat4=cat4,cat5=cat5,cat6=cat6,cat7=cat7,cat8=cat8,cat9=cat9,cat10=cat10,cat11=cat11,cat12=cat12,cat13=cat13,cat14=cat14,cat15=cat15)






