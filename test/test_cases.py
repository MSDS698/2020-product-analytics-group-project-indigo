import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application import db, User, application


def UserFromDB(username):
    """
    Function that returns the user with given username from the database
    """
    user = User.query.filter_by(username=username).first()
    return user


@pytest.fixture(scope='module')
def client():
    basedir = os.path.abspath(os.path.dirname(__file__))
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir,
                                                            'test.db'),
        WTF_CSRF_ENABLED=False)

    with application.test_client() as c:
        yield c


@pytest.fixture(scope='module')
def init_database():
    db.create_all()

    user1 = User('post malone', 'post@gmail.com', 'watermalone')
    user2 = User('tester', 'test@test.com', 'test123')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    yield db

    db.drop_all()


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


def test_login_success(client, init_database):
    response = client.post('/login', data=dict(username='post malone',
                                               password='watermalone'),
                           follow_redirects=True)
    assert response.status_code == 200
    assert b'GET STARTED' in response.data
    assert b'Login' not in response.data


def test_login_username_failure(client, init_database):
    response = client.post('/login', data=dict(username='test',
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    # assert b'Username not found' in response.data


def test_login_password_failure(client, init_database):
    response = client.post('/login', data=dict(username='post malone',
                                               password='test123'),
                           follow_redirects=True)
    assert b'Login' in response.data
    assert b'Username' in response.data
    # assert b'Incorrect password' in response.data


def test_login_unregistered(client, init_database):
    pass


def register_duplicate_email(client, init_database):
    response = client.post('register', data=dict(username='duplicate',
                                                 email='post@gmail.com',
                                                 password='123456',
                                                 confirm='123456',
                                                 accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data


def register_duplicate_username(client, init_database):
    response = client.post('register', data=dict(username='post malone',
                                                 email='NOTpost@gmail.com',
                                                 password='123456',
                                                 confirm='123456',
                                                 accept_tos='y'),
                           follow_redirects=True)
    assert b'Repeat Password' in response.data


def test_create_user():
    """
    Function that creates a user and checks that the username, email, and
    password have been stored correctly in the database
    """
    assert UserFromDB('post malone').username == 'post malone'
    assert UserFromDB('post malone').email == 'post@gmail.com'
    assert UserFromDB('post malone').check_password('watermalone')
    assert UserFromDB('post malone').password_hash != 'watermalone'


def test_create_two_users():
    """
    Function that creates two users and checks that individual user details can
    be correctly returned from the database
    """
    assert not UserFromDB('tester').username == 'post malone'
    assert UserFromDB('tester').email == 'test@test.com'
    assert not UserFromDB('tester').check_password('watermalone')

