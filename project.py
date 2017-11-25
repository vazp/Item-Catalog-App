#!/usr/bin/env python
"""Item catalog project"""
import json
import random
import string
import sys
from os import makedirs
from os import path
from os import rename
from os import remove
from flask import abort
from flask import Flask
from flask import flash
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import session as login_session
from flask import url_for
from functools import wraps
from sqlalchemy import asc
from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy import exists
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import and_
from oauth2client import client
from db_model import BASE
from db_model import Category
from db_model import Item
from db_model import User


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

if path.isfile('client_secrets.json') is False:
    sys.exit('client_secrets.json not found.')

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())[
    'web']['client_id']

ENGINE = create_engine('sqlite:///catalog.db')
BASE.metadata.bind = ENGINE

DBSESSION = sessionmaker(bind=ENGINE)
SESSION = DBSESSION()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Check if a filename is a valid one"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_user(login_session):
    """Creates and adds a new user to the database"""
    new_user = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    SESSION.add(new_user)
    SESSION.commit()
    user = SESSION.query(User).filter_by(email=login_session['email']).one()
    return user.id_user


def get_user_info(user_id):
    """Given a user id, returns the user"""
    user = SESSION.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    """Given a user's email, returns the user id"""
    try:
        user = SESSION.query(User).filter_by(email=email).one()
        return user.id_user
    except:
        return None


def get_random_code():
    """Generates a random 5 character code"""
    code = ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in xrange(5))
    return code


def login_required(f):
    @wraps(f)
    def check_for_login(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash('You are not allowed to access this content')
            return redirect(url_for('show_catalog'))
    return check_for_login


@app.errorhandler(404)
def page_not_found(e):
    """404 page"""
    return render_template('404.html'), 404


@app.route('/uploads/<path:filename>')
def uploads(filename):
    """Route for uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Use google services to log in and get user information"""
    id_token = request.form.get('id_token', '')
    idinfo = client.verify_id_token(id_token, CLIENT_ID)
    if idinfo['iss'] not in ['accounts.google.com',
                             'https://accounts.google.com']:
        return make_response('Wrong Issuer.', 401)

    guser_id = idinfo['sub']

    stored_id_token = login_session.get('id_token')
    stored_g_id = login_session.get('google_id')

    if stored_id_token is not None and guser_id == stored_g_id:
        flash('Already logged in')
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['id_token'] = id_token
    login_session['google_id'] = guser_id

    login_session['username'] = idinfo['name']
    login_session['picture'] = idinfo['picture']
    login_session['email'] = idinfo['email']

    user_id = get_user_id(idinfo['email'])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    response = make_response(json.dumps('Login successful.'), 200)
    response.headers['Content-Type'] = 'application/json'
    flash("Now logged in as %s" % login_session['username'])
    return response


@app.route('/gdisconnect')
def gdisconnect():
    """Log out of the application"""
    id_token = login_session.get('id_token')
    if id_token is None:
        flash("Not connected")
        response = make_response(json.dumps(
            'Current user not connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    del login_session['id_token']
    del login_session['google_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    flash('You have been successfully logged out')
    return response


@app.route('/catalog/JSON')
def catalog_json():
    """Endpoint that returns the whole catalog in JSON format"""
    categories = SESSION.query(Category).order_by(asc(Category.name)).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/catalog/<string:category_slug>/items/JSON')
def category_json(category_slug):
    """Endpoint that returns all the items for a given category in JSON
       format"""
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()
    if not selected_category:
        return jsonify()
    items = SESSION.query(Item).filter_by(
        id_category=selected_category.id_category) \
        .order_by(asc(Item.name)).all()

    return jsonify(items=[i.serialize for i in items])


@app.route('/catalog/<string:category_slug>/items/<string:item_slug>/JSON')
def item_json(category_slug, item_slug):
    """Endpoint that returns the information for a given item in JSON format"""
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()
    if not selected_category:
        return jsonify()
    selected_item = SESSION.query(Item).filter_by(
        slug=item_slug, id_category=selected_category.id_category).first()
    if not selected_item:
        return jsonify()
    return jsonify(item=selected_item.serialize)


@app.route('/')
def redirect_catalog():
    """ Route that redirects to catalog """
    return redirect(url_for('show_catalog'))


@app.route('/catalog')
def show_catalog():
    """Displays the main page with all the categories and the latest added
       items"""
    categories = SESSION.query(Category).order_by(asc(Category.name)).all()
    latest_items = SESSION.query(Item).order_by(
        desc(Item.id_item)).limit(5).all()
    if 'username' not in login_session:
        return render_template('publiccatalog.html', categories=categories,
                               items=latest_items)
    else:
        return render_template('catalog.html', categories=categories,
                               items=latest_items)


@app.route('/catalog/<string:category_slug>/items')
def show_category(category_slug):
    """Displays all the items for the selected category"""
    categories = SESSION.query(Category).order_by(asc(Category.name)).all()
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()
    if not selected_category:
        abort(404)
    items = SESSION.query(Item).filter_by(
        id_category=selected_category.id_category) \
        .order_by(asc(Item.name)).all()

    if 'username' not in login_session:
        return render_template('publiccategory.html', categories=categories,
                               selected_category=selected_category.name,
                               items=items)
    else:
        return render_template('category.html', categories=categories,
                               selected_category=selected_category.name,
                               items=items)


@app.route('/catalog/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """ Add a new category to the database """
    if request.method == 'POST':
        category_name = request.form['categoryName']
        if category_name:
            category_slug = category_name.lower().replace(' ', '-')
            if not SESSION.query(exists().where(Category.slug ==
                                                category_slug)).scalar():
                category = Category(
                    slug=category_slug, name=category_name,
                    id_user=login_session['user_id'])
                SESSION.add(category)
                SESSION.commit()
                flash('Category successfully created')
                return redirect(url_for('show_catalog'))
            else:
                flash('There is already a category with that name')
                return redirect(request.referrer)
        else:
            flash('Something went wrong while creating the category')
            return redirect(url_for('show_catalog'))
    else:
        return render_template('newcategory.html')


@app.route('/catalog/<string:category_slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_slug):
    """Edit a category"""
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()

    if not selected_category:
        abort(404)

    if selected_category.id_user != login_session['user_id']:
        flash('You are not authorized to edit this category')
        return redirect(url_for('show_catalog'))

    if request.method == 'POST':
        category_name = request.form['categoryName']
        if category_name:
            if selected_category.name == category_name:
                return redirect(url_for('show_catalog'))
            new_category_slug = category_name.lower().replace(' ', '-')
            if not SESSION.query(exists().where(Category.slug ==
                                                new_category_slug)).scalar():
                selected_category.name = category_name
                selected_category.slug = new_category_slug
                SESSION.commit()
                flash('Category successfully edited')
                return redirect(url_for('show_catalog'))
            else:
                flash('There is already a category with that name')
                return redirect(request.referrer)
        else:
            flash('Something went wrong while editing the category')
            return redirect(url_for('show_catalog'))
    else:
        return render_template('editcategory.html', category=selected_category)


@app.route('/catalog/<string:category_slug>/delete', methods=['GET', 'POST'])
@login_required
def delete_category(category_slug):
    """Delete a category and all of its associated items"""
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()

    if not selected_category:
        abort(404)

    if selected_category.id_user != login_session['user_id']:
        flash('You are not authorized to delete this category')
        return redirect(url_for('show_catalog'))

    if request.method == 'POST':
        for item in selected_category.items:
            if item.image is not None:
                try:
                    remove(path.join(app.config['UPLOAD_FOLDER'], item.image))
                except:
                    flash('Something went wrong with the image')

        SESSION.delete(selected_category)
        SESSION.commit()
        flash('Category successfully deleted')
        return redirect(url_for('show_catalog'))
    else:
        return render_template('deletecategory.html',
                               category=selected_category)


@app.route('/catalog/<string:category_slug>/items/<string:item_slug>')
def show_item(category_slug, item_slug):
    """Displays an item information"""
    selected_category = SESSION.query(
        Category).filter_by(slug=category_slug).first()
    if not selected_category:
        abort(404)
    selected_item = SESSION.query(Item).filter_by(
        slug=item_slug, id_category=selected_category.id_category).first()
    if not selected_item:
        abort(404)

    if 'username' not in login_session:
        return render_template('publicitem.html', item=selected_item)
    else:
        return render_template('item.html', item=selected_item)


@app.route('/catalog/item/new', methods=['GET', 'POST'])
@login_required
def new_item():
    """Add a new item to the database"""
    if request.method == 'POST':
        item_name = request.form['itemName']
        if item_name:
            item_slug = item_name.lower().replace(' ', '-')
            category_id = request.form['itemCategory']

            selected_category = SESSION.query(Category).filter_by(
                id_category=category_id).first()

            if SESSION.query(exists().where(and_(Item.id_category ==
                                                 category_id, Item.slug ==
                                                 item_slug))).scalar():
                flash('There is already an item with that name')
                return redirect(request.referrer)

            item_description = request.form['itemDescription']
            item_img = None
            rng_code = None

            image_file = request.files['itemImg']
            if image_file and allowed_file(image_file.filename):
                file_name = selected_category.slug + '__' + item_slug + '.jpg'
                item_img = file_name
                rng_code = get_random_code()
                if not path.exists(app.config['UPLOAD_FOLDER']):
                    makedirs(app.config['UPLOAD_FOLDER'])
                image_file.save(path.join(app.config['UPLOAD_FOLDER'],
                                          file_name))

            item = Item(id_category=category_id, image=item_img,
                        random_string=rng_code, slug=item_slug, name=item_name,
                        description=item_description,
                        id_user=login_session['user_id'])
            SESSION.add(item)
            SESSION.commit()

            flash('Item successfully created')
            return redirect(url_for('show_catalog'))

        else:
            flash('Something went wrong')
            return redirect(url_for('show_catalog'))

    else:
        categories = SESSION.query(Category).order_by(asc(Category.name)).all()

        if not categories:
            flash('You must first create a category')
            return redirect(url_for('show_catalog'))

        return render_template('newitem.html', categories=categories)


@app.route('/catalog/<string:category_slug>/items/<string:item_slug>/edit',
           methods=['GET', 'POST'])
@login_required
def edit_item(category_slug, item_slug):
    """Edit an item"""
    category = SESSION.query(Category).filter_by(slug=category_slug).first()

    if not category:
        abort(404)

    selected_item = SESSION.query(Item).filter_by(
        slug=item_slug, id_category=category.id_category).first()

    if not selected_item:
        abort(404)

    if selected_item.id_user != login_session['user_id']:
        flash('You are not authorized to edit this item')
        return redirect(url_for('show_catalog'))

    if request.method == 'POST':
        item_name = request.form['itemName']
        new_item_slug = item_name.lower().replace(' ', '-')
        if item_name:
            category = SESSION.query(Category).filter_by(
                slug=category_slug).first()
            selected_item = SESSION.query(Item).filter_by(
                slug=item_slug, id_category=category.id_category).first()

            # Check every field for changes
            item_category_id = int(request.form['itemCategory'])
            should_change_image_name = False
            if item_category_id != selected_item.id_category:
                if not SESSION.query(exists()
                                     .where(and_(Item.id_category ==
                                                 item_category_id,
                                                 Item.slug ==
                                                 new_item_slug))).scalar():
                    selected_item.id_category = item_category_id
                    category = SESSION.query(Category).filter_by(
                        id_category=item_category_id).first()
                    should_change_image_name = True
                else:
                    SESSION.rollback()
                    flash('There is already an item with this name on this \
                           category')
                    return redirect(url_for('show_catalog'))

            if item_name != selected_item.name:
                if not SESSION.query(exists()
                                     .where(and_(Item.id_category ==
                                                 item_category_id,
                                                 Item.slug ==
                                                 new_item_slug))).scalar():
                    selected_item.name = item_name
                    selected_item.slug = new_item_slug
                    should_change_image_name = True
                else:
                    SESSION.rollback()
                    flash('There is already an item with this name on this \
                           category')
                    return redirect(url_for('show_catalog'))

            if selected_item.image is not None and should_change_image_name:
                old_image = path.join(
                    app.config['UPLOAD_FOLDER'], selected_item.image)
                new_image_name = category.slug + '__' + new_item_slug + '.jpg'
                try:
                    rename(old_image, path.join(
                        app.config['UPLOAD_FOLDER'], new_image_name))
                    selected_item.image = new_image_name
                except:
                    SESSION.rollback()
                    flash('Something went wrong')
                    return redirect(request.referrer)

            image_file = request.files['itemImg']
            if image_file and allowed_file(image_file.filename):
                file_name = category.slug + '__' + new_item_slug + '.jpg'
                selected_item.random_string = get_random_code()
                if not path.exists(app.config['UPLOAD_FOLDER']):
                    makedirs(app.config['UPLOAD_FOLDER'])
                image_file.save(path.join(app.config['UPLOAD_FOLDER'],
                                          file_name))

            item_description = request.form['itemDescription']
            selected_item.description = item_description

            SESSION.commit()
            flash('Item successfully edited')
            return redirect(url_for('show_catalog'))
        else:
            flash('Something went wrong')
            return redirect(url_for('show_catalog'))

    else:
        categories = SESSION.query(Category).order_by(asc(Category.name)).all()

        if not categories:
            flash('You must first create a category')
            return redirect(url_for('show_catalog'))

        return render_template('edititem.html', categories=categories,
                               item=selected_item)


@app.route('/catalog/<string:category_slug>/items/<string:item_slug>/delete',
           methods=['GET', 'POST'])
@login_required
def delete_item(category_slug, item_slug):
    """Delete an item"""
    category = SESSION.query(Category).filter_by(slug=category_slug).first()

    if not category:
        abort(404)

    selected_item = SESSION.query(Item).filter_by(
        slug=item_slug, id_category=category.id_category).first()

    if not selected_item:
        abort(404)

    if selected_item.id_user != login_session['user_id']:
        flash('You are not authorized to delete this item')
        return redirect(url_for('show_catalog'))

    if request.method == 'POST':
        if selected_item.image is not None:
            try:
                remove(path.join(app.config['UPLOAD_FOLDER'],
                                 selected_item.image))
            except:
                flash('Something went wrong with the image')

        SESSION.delete(selected_item)
        SESSION.commit()
        flash('Item successfully deleted')
        return redirect(url_for('show_catalog'))

    else:
        return render_template('deleteitem.html', item=selected_item)


if __name__ == '__main__':
    app.secret_key = 's3Cr3T_k3Y'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
