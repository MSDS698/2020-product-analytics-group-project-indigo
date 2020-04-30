import csv
import os
import sys
from datetime import datetime

from config import Config
from flask import render_template, redirect, url_for, request, flash, Flask
from flask_login import LoginManager, UserMixin, current_user, login_user, \
    login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
#from flask_bootstrap import Bootstrap
from wtforms import BooleanField, DateField, IntegerField, SelectField, \
    SubmitField, PasswordField, StringField, validators, Form
from wtforms.validators import DataRequired
from werkzeug.security import check_password_hash, generate_password_hash

import boto3

ALLOWED_EXTENSIONS = {'midi', 'mid'}

on_dev = True

# Initialization
# Create an application instance which handles all requests.
application = Flask(__name__)
application.secret_key = os.urandom(24)
application.config.from_object(Config)

db = SQLAlchemy(application)
db.create_all()
db.session.commit()

#bootstrap = Bootstrap(application)

# login_manager needs to be initiated before running the app
login_manager = LoginManager()
login_manager.init_app(application)


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
    """Class for register a new user."""
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])
    submit = SubmitField('Submit')


class LogInForm(FlaskForm):
    """Class for login form"""
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


class Customer(db.Model, UserMixin):
    """Class for user object"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Files(db.Model, UserMixin):
    """File class with file and user properties for database"""

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(80), nullable=False)
    orig_filename = db.Column(db.String(120), nullable=False)
    file_type = db.Column(db.String(120), nullable=False)  # mid or mp3 etc
    # gan, user_upload, rnn, vae, etc
    model_used = db.Column(db.String(120), nullable=False)
    our_filename = db.Column(db.String(80), unique=True, nullable=False)
    file_upload_timestamp = db.Column(db.String(120), nullable=False)

    def __init__(self, user_name, orig_filename, file_type, model_used,
                 our_filename, file_upload_timestamp):
        self.user_name = user_name
        self.orig_filename = orig_filename
        self.file_type = file_type
        self.model_used = model_used
        self.our_filename = our_filename
        self.file_upload_timestamp = file_upload_timestamp


db.create_all()
db.session.commit()


@login_manager.user_loader
def load_user(id):
    """
    This callback is used to reload the user object
    from the user ID stored in the session.
    """
    return Customer.query.get(int(id))


def allowed_file(filename):
    """Checks if file is of allowed type"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/index')
@application.route('/')
def index():
    """Index Page : Renders index.html with author names."""
    return (render_template('index.html'))


@application.route('/register',  methods=['GET', 'POST'])
def register():
    """Register function that writes new user to SQLite DB"""
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():
        username = registration_form.username.data
        password = registration_form.password.data
        email = registration_form.email.data

        user_count = Customer.query.filter_by(username=username).count() \
            + Customer.query.filter_by(email=email).count()
        if user_count > 0:
            flash('Username or email already exists')
        else:
            user = Customer(username, email, password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', form=registration_form)


@application.route('/login', methods=['GET', 'POST'])
def login():
    """Login function that takes in username and password."""
    login_form = LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = Customer.query.filter_by(username=username).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('profile'))
        else:
            flash('Incorrect Password')

    return render_template('login.html', form=login_form)


@application.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('index'))

@application.route('/create')
@login_required
def start():
    return render_template('create.html')

@application.route('/profile')
@login_required
def profile():
    uploads = Files.query.filter_by(user_name=current_user.username).all()
    return render_template('profile.html', uploads=uploads, username=current_user.username)


@application.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """
    Upload a file from a client machine to
    s3 and file properties to Database
    """
    file = UploadFileForm()  # file : UploadFileForm class instance
    uploads = Files.query.filter_by(user_name=current_user.username).all()
    
    # Check if it is a POST request and if it is valid.
    if file.validate_on_submit():
        f = file.file_selector.data  # f : Data of FileField
        filename = f.filename
        # filename : filename of FileField
        if not allowed_file(filename):
            flash('Incorrect File Type')
            return redirect(url_for('upload'))

        # make directory and save files there
        cwd = os.getcwd()

        file_dir_path = os.path.join(cwd, 'files')

        if not os.path.exists(file_dir_path):
            os.mkdir(file_dir_path)

        file_path = os.path.join(file_dir_path, filename)

        f.save(file_path)


        user_name = current_user.username
        orig_filename = filename.rsplit('.', 1)[0]
        file_type = filename.rsplit('.', 1)[1]
        model_used = 'user_upload'

        # get num of files user has uploaded thus far
        num_user_files = Files.query.filter_by(user_name=user_name).count()
        our_filename = f'{user_name}_{num_user_files}'
        file_upload_timestamp = datetime.now()

        file = Files(user_name, orig_filename, file_type,
                     model_used, our_filename, file_upload_timestamp)
        db.session.add(file)
        db.session.commit()

        # TAKES CARE OF DEV OR local
        if on_dev:
            s3 = boto3.resource('s3')
            s3.meta.client.upload_file(file_path, 'midi-file-upload', our_filename)

        # USE FOR REMOTE - msds603 is my alias in ./aws credentials file using
        # secret key from iam on jacobs account
        else:
           session = boto3.Session(profile_name='msds603') 
           dev_s3_client = session.resource('s3')
           dev_s3_client.meta.client.upload_file(file_path, 'midi-file-upload', filename)


        if os.path.exists(file_dir_path):
            os.system(f"rm -rf {file_dir_path}")
            
        

        return redirect(url_for('music'))  # Redirect to / (/index) page.

    return render_template('upload.html', form=file, uploads=uploads)


@application.route('/demo', methods=['GET', 'POST'])
def demo():
    """ Load demo page showing Magenta """
    return render_template('demo.html')


@application.route('/about', methods=['GET', 'POST'])
def about():
    """Load About page"""
    return render_template('about.html')


@application.route('/music', methods=['GET', 'POST'])
@login_required
def music():
    uploads = Files.query.filter_by(user_name=current_user.username).all()
    
    return render_template('music.html', uploads=uploads)


@application.route('/create', methods=['GET', 'POST'])
def create():
    return render_template('create.html')

@application.route('/buy', methods=['GET', 'POST'])
def buy():
    return render_template('buy.html')

@application.route('/my_music', methods=['GET', 'POST'])
def my_music():
    return render_template('my_music.html')


@application.route('/test_playback/<filename>', methods=['GET', 'POST'])
def test_playback(filename):
    # uncomment the next 2 lines when on local

    # session = boto3.Session(profile_name='msds603') # insert your profile name
    # s3 = session.resource('s3')
    if on_dev:
        s3 = boto3.resource('s3') # comment out when on local
    #LOCAL
    else:
        session = boto3.Session(profile_name='msds603') # insert your profile name
        s3 = session.resource('s3')

    object = s3.Object('midi-file-upload', filename)

    #binary_body = object.get()['Body'].read()
    #return render_template('test_playback.html', midi_binary=binary_body)

    # make directory and save files there
    file_dir_path = './static/tmp'

    if not os.path.exists(file_dir_path):
        os.mkdir(file_dir_path)

    object.download_file(f'./static/tmp/{filename}.mid')

    return render_template('test_playback.html', midi_file=filename+'.mid')


@application.route('/drums', methods=['GET', 'POST'])
def drums():
    return render_template('drums.html')

if __name__ == '__main__':
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.debug = True
    application.run()
