from flask import Flask
from flask import render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField, PasswordField, StringField, BooleanField, validators, Form
import csv
import os
from config import Config

ALLOWED_EXTENSIONS = {'midi', 'mid'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
application = Flask(__name__)
application.secret_key = os.urandom(24)

application.config.from_object(Config)

#db = SQLAlchemy(application)
#db.create_all()
#db.session.commit()


class UploadFileForm(FlaskForm):
    """Class for uploading file when submitted"""
    file_selector = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')

class RegistrationForm(Form):
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


if __name__ == '__main__':
    application.jinja_env.auto_reload = True
    application.config['TEMPLATES_AUTO_RELOAD'] = True
    application.debug = True
    application.run()
