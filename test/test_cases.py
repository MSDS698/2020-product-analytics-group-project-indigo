import pytest
import io
import os
import subprocess
from application import application, db, Customer, Files

TEST_USER = dict(user='TEST_USER',
                 email='test@gmail.com',
                 password='testpass')


@pytest.fixture(scope='module')
def client():
    """
    Starts Flask test client
    """
    application.config.update(TESTING=True,
                              WTF_CSRF_ENABLED=False)
    test_client = application.test_client()
    yield test_client


@pytest.fixture(scope='module')
def init_database(client):
    """
    Yields postgres db for testing
    """
    yield db


def UserFromDB(username):
    """
    Function that returns the user with given username from the database
    """
    user = Customer.query.filter_by(username=username).first()
    return user


def FileFromDB(username):
    """
    Function that returns the file for a given username
    """
    files = Files.query.filter_by(user_name=username).first()
    return files


def test_home(client):
    """
    Tests that homepage is up and running
    """
    response = client.get('/')
    # 200 is success status code
    assert response.status_code == 200
    assert b'INDIGO' in response.data


def test_login(client):
    """
    Tests that login page is up and running
    """
    response = client.get('/login')
    # 200 is success status code
    assert response.status_code == 200
    assert b'Username' in response.data
    assert b'Password' in response.data


def test_register(client):
    """
    Tests that register page is up and running
    """
    response = client.get('/register')
    # 200 is success status code
    assert response.status_code == 200
    assert b'Email Address' in response.data
    assert b'New Password' in response.data


def test_music_not_logged_in(client):
    """
    Tests that user not logged in cannot access the music page
    """
    response = client.get('/profile/' + TEST_USER['user'])
    # 302 is redirected status code
    # page redirect to login
    assert response.status_code == 302


def test_register_test_user(client):
    """
    Registers the test user and checks that is was successful
    """
    response = client.post('/register', data=dict(username=TEST_USER['user'],
                                                  email=TEST_USER['email'],
                                                  password=TEST_USER
                                                  ['password'],
                                                  confirm=TEST_USER
                                                  ['password'],
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b'INDIGO- Login' in response.data


def test_login_test_user(client, init_database):
    """
    Tests login of that test user
    """
    response = client.post('/login', data=dict(username=TEST_USER['user'],
                                               password=TEST_USER['password']),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b'Discover Users:' in response.data
    assert b'Drums' in response.data


def test_login_username_failure(client, init_database):
    """
    Tests that an incorrect username cannot log in.
    App needs an error message for users
    """
    response = client.post('/login', data=dict(username='iklsjts',
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    # assert b'Username not found' in response.data


def test_login_password_failure(client, init_database):
    """
    Tests than an incorrect password cannot log in.
    App needs an error message for users
    """
    response = client.post('/login', data=dict(username=TEST_USER['user'],
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    assert b'Incorrect Password' in response.data


def test_login_unregistered(client, init_database):
    """
    Tests that unregistered user cannot log in.
    App needs error message and redirect to register page.
    Needs to be implemented.
    """
    pass


def register_duplicate_email(client, init_database):
    """
    Tests that a duplicate email cannot register
    App needs better error messaging for the user
    """
    response = client.post('/register', data=dict(username='duplicate',
                                                  email='test@gmail.com',
                                                  password='123456',
                                                  confirm='123456',
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data
    assert b'Username or email already exists'


def register_duplicate_username(client, init_database):
    """
    Tests that a duplicate username cannot register
    App needs better error messaging for the user
    """
    response = client.post('/register', data=dict(username=TEST_USER['user'],
                                                  email='something@gmail.com',
                                                  password='123456',
                                                  confirm='123456',
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data
    assert b'Username or email already exists'


def test_file_upload(client, init_database):
    """
    Tests that a logged in user can upload a file.
    Try/except to catch errors with s3 access
    """
    # Delete files from our user already in DB, in case one exists
    Files.query.filter_by(user_name=TEST_USER['user']).delete()
    db.session.commit()
    client.post('/login', data=dict(username=TEST_USER['user'],
                                    password=TEST_USER['password']),
                follow_redirects=True)
    response = client.post('/upload', data=dict(
        file_selector=(io.BytesIO(b"test string"), 'Queen_test.mid')),
                           follow_redirects=True,
                           content_type='multipart/form-data')
    assert b'Discover Users:' in response.data
    assert FileFromDB(TEST_USER['user']).orig_filename == 'Queen_test'
    assert FileFromDB(TEST_USER['user']).our_filename.\
        startswith(TEST_USER['user'])
    # Deletes the uploaded test file entry from postgres
    Files.query.filter_by(user_name=TEST_USER['user']).delete()
    db.session.commit()


def test_drums_VAE_pages(client, init_database):
    """
    Tests that a logged in user can upload a file.
    Try/except to catch errors with s3 access
    """
    client.post('/login', data=dict(username=TEST_USER['user'],
                                    password=TEST_USER['password']),
                follow_redirects=True)
    response = client.get('/drums-upload')
    response1 = client.get('/vae-upload')
    assert response.status_code == 200
    assert response1.status_code == 200


def test_logout_logged_in_user(client, init_database):
    """
    Tests that a user can logout and is redirected to the home page
    """
    client.post('/login', data=dict(username=TEST_USER['user'],
                                    password=TEST_USER['password']),
                follow_redirects=True)
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'LOGIN' in response.data


def test_logout_logged_out_user(client, init_database):
    """
    Tests that a user not logged in cannot log out
    """
    response = client.get('/logout')
    # 302 is redirected status code
    assert response.status_code == 302


def test_remove_test_user(init_database):
    """
    Removes our test user from the Customer db as our testing is complete
    """
    Customer.query.filter_by(username=TEST_USER['user']).delete()
    db.session.commit()
    assert UserFromDB(TEST_USER['user']) is None


def test_pep8():
    """
    Tests that all .py files in the main directory follow PEP8 style guidelines
    """
    path = os.path.dirname(os.path.abspath(__file__))
    with open(path + '/pep8.sh', 'r') as f:
        script = f.read()
    pep8_output = subprocess.check_output(script, shell=True).decode("utf-8")
    assert 'E' not in pep8_output
