import csv
import os

from config import Config
from flask import render_template, redirect, url_for, request, flash, Flask
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import BooleanField, DateField, IntegerField, SelectField, SubmitField, PasswordField, StringField, validators, Form
from wtforms.validators import DataRequired
from werkzeug.security import check_password_hash, generate_password_hash

ALLOWED_EXTENSIONS = {'midi', 'mid'}


# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
application = Flask(__name__)
application.secret_key = os.urandom(24)
application.config.from_object(Config)

# db = SQLAlchemy(application)
# db.create_all()
# db.session.commit()

# # login_manager needs to be initiated before running the app
# login_manager = LoginManager()
# login_manager.init_app(application)


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
    username = StringField('Username:', validators=[DataRequired()])
    password = PasswordField('Password:', validators=[DataRequired()])
    submit = SubmitField('Login')

class User(db.Model, UserMixin):
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


# user_loader :
# This callback is used to reload the user object
# from the user ID stored in the session.
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/index')
@application.route('/')
def index():
    """Index Page : Renders index.html with author names."""
    return (render_template('index.html'))


@application.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register a new user. Save the username, password and email.
    """
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        # user = User(form.username.data, form.email.data,
        #             form.password.data)
        with open('users.csv', mode='w+', newline='') as accounts_file:
            accounts_writer = csv.writer(accounts_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            accounts_writer.writerow([form.username.data, form.email.data, form.password.data])
        # db_session.add(user)
        flash('Thanks for registering')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


# @application.route('/register',  methods=('GET', 'POST'))
# def register():
#     registration_form = RegistrationForm()
#     if registration_form.validate_on_submit():
#         username = registration_form.username.data
#         password = registration_form.password.data
#         email = registration_form.email.data

#         user_count = User.query.filter_by(username=username).count() \
#                      + User.query.filter_by(email=email).count()
#         if (user_count > 0):
#             return '<h1>Error - Existing user : ' + username \
#                    + ' OR ' + email + '</h1>'
#         else:
#             user = User(username, email, password)
#             db.session.add(user)
#             db.session.commit()
#             return redirect(url_for('index'))
#     return render_template('register.html', form=registration_form)


@application.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LogInForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Look for it in the database.
        user = User.query.filter_by(username=username).first()

        # Login and validate the user.
        if user is not None and user.check_password(password):
            login_user(user)
            return redirect(url_for('register_project'))

    return render_template('login.html', form=login_form)




@application.route('/upload', methods=['GET', 'POST'])
def upload():
    """upload a file from a client machine."""
    file = UploadFileForm()  # file : UploadFileForm class instance
    if file.validate_on_submit():  # Check if it is a POST request and if it is valid.
        f = file.file_selector.data  # f : Data of FileField
        filename = f.filename
        # filename : filename of FileField
        if not allowed_file(filename):
            return ("<h1> Incorrect File Type </h1>")
        file_dir_path = os.path.join(application.instance_path, 'files')
        file_path = os.path.join(file_dir_path, filename)
        f.save(file_path) # Save file to file_path (instance/ + 'files’ + filename)

        return redirect(url_for('index'))  # Redirect to / (/index) page.
    return render_template('upload.html', form=file)


@application.route('/demo', methods=['GET', 'POST'])
def demo():
    """ Load demo page showing Magenta """
    return render_template('demo.html')

@application.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@application.route('/music', methods=['GET', 'POST'])
def music():
    return render_template('music.html')

if __name__ == '__main__':
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.debug = True
    application.run()
