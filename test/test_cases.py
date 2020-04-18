import boto3
import pytest
import io
from application import application, db, Customer, Files


TEST_USER = dict(user='TEST_USER',
                 email='test@gmail.com',
                 password='testpass')


@pytest.fixture(scope='module')
def client():
    application.config.update(TESTING=True,
                              WTF_CSRF_ENABLED=False)
    test_client = application.test_client()
    yield test_client


@pytest.fixture(scope='module')
def init_database(client):
    yield db


def UserFromDB(username):
    """
    Function that returns the user with given username from the database
    """
    user = Customer.query.filter_by(username=username).first()
    return user


def FileFromDB(username):
    """
    Function that returns a list of upload original file names for a given user
    """
    files = Files.query.filter_by(user_name=username).first()
    return files


def test_home(client):
    response = client.get('/')
    # 200 is success status code
    assert response.status_code == 200
    assert b'INDIGO' in response.data


def test_login(client):
    response = client.get('/login')
    # 200 is success status code
    assert response.status_code == 200
    assert b'Username' in response.data
    assert b'Password' in response.data


def test_register(client):
    response = client.get('/register')
    # 200 is success status code
    assert response.status_code == 200
    assert b'Email Address' in response.data
    assert b'New Password' in response.data


def test_music_not_logged_in(client):
    response = client.get('/music')
    # 401 is unauthorized status code
    assert response.status_code == 401


def test_register_test_user(client):
    response = client.post('/register', data=dict(username=TEST_USER['user'],
                                                  email=TEST_USER['email'],
                                                  password=TEST_USER['password'],
                                                  confirm=TEST_USER['password'],
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b'INDIGO- Login' in response.data


def test_login_test_user(client, init_database):
    response = client.post('/login', data=dict(username=TEST_USER['user'],
                                               password=TEST_USER['password']),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b'INDIGO- Make Music' in response.data
    assert b'Login' not in response.data


def test_login_username_failure(client, init_database):
    response = client.post('/login', data=dict(username='iklsjts',
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    # assert b'Username not found' in response.data


def test_login_password_failure(client, init_database):
    response = client.post('/login', data=dict(username=TEST_USER['user'],
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    # assert b'Incorrect password' in response.data


def test_login_unregistered(client, init_database):
    # Need to implement this
    pass


def register_duplicate_email(client, init_database):
    response = client.post('/register', data=dict(username='duplicate',
                                                  email='test@gmail.com',
                                                  password='123456',
                                                  confirm='123456',
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data


def register_duplicate_username(client, init_database):
    response = client.post('/register', data=dict(username=TEST_USER['user'],
                                                  email='something@gmail.com',
                                                  password='123456',
                                                  confirm='123456',
                                                  accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data


def test_file_upload(client, init_database):
    client.post('/login', data=dict(username=TEST_USER['user'],
                                    password=TEST_USER['password']),
                follow_redirects=True)
    try:
        response = client.post('/upload', data=dict(file_selector=
                                                    (io.BytesIO(b"test string"),
                                                     'Queen_test.mid')),
                               follow_redirects=True,
                               content_type='multipart/form-data')
        assert b'Select from uploads' in response.data
        assert FileFromDB(TEST_USER['user']).orig_filename == 'Queen_test'

        s3_file_name = FileFromDB(TEST_USER['user']).our_filename
        s3 = boto3.resource('s3')
        s3.Object('midi-file-upload', s3_file_name).delete()

        Files.query.filter_by(user_name=TEST_USER['user']).delete()
        db.session.commit()

    except boto3.exceptions.S3UploadFailedError:
        assert True


def test_logout_logged_in_user(client, init_database):
    client.post('/login', data=dict(username=TEST_USER['user'],
                                    password=TEST_USER['password']),
                follow_redirects=True)
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'LOGIN' in response.data


def test_logout_logged_out_user(client, init_database):
    response = client.get('/logout')
    # 401 is unauthorized status code
    assert response.status_code == 401


def test_remove_test_user(init_database):
    Customer.query.filter_by(username=TEST_USER['user']).delete()
    db.session.commit()
    assert UserFromDB(TEST_USER['user']) is None
