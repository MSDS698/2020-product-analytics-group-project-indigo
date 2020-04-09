import os
import sys
from sqlalchemy import or_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application import db, User


def UserFromDB(username):
    """
    Function that returns the user with given username from the database
    """
    user = User.query.filter_by(username=username).first()
    return user


def test_login_success():
    pass


def test_login_incorrect_password():
    pass


def test_login_incorrect_username():
    pass


def test_login_unregistered():
    pass


def test_create_user():
    """
    Function that creates a user and checks that the username, email, and
    password have been stored correctly in the database
    """
    db.create_all()
    user1 = User('post malone', 'post@gmail.com', 'watermalone')
    # delete existing 'post malone' user before adding new one to avoid
    # sqlalchemy db integrity error 'unique constraint'
    User.query.filter_by(username=user1.username). \
        delete(synchronize_session='fetch')
    db.session.add(user1)
    db.session.commit()
    assert UserFromDB('post malone').username == 'post malone'
    assert UserFromDB('post malone').email == 'post@gmail.com'
    assert UserFromDB('post malone').check_password('watermalone')


def test_create_two_users():
    """
    Function that creates two users and checks that indivdual user details can
    be correctly returned from the database
    """
    db.create_all()
    user1 = User('tester', 'test@test.com', 'test123')
    user2 = User('post malone', 'post@gmail.com', 'watermalone')
    # delete existing 'post malone' user before adding new one to avoid
    # sqlalchemy db integrity error 'unique constraint'
    User.query.filter(or_(User.username == user1.username,
                          User.username == user1.username)).\
        delete(synchronize_session='fetch')
    db.session.add(user1, user2)
    db.session.commit()
    assert not UserFromDB('tester').username == 'post malone'
    assert UserFromDB('tester').email == 'test@test.com'
    assert not UserFromDB('tester').check_password('watermalone')
