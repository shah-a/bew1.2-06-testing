from unittest import TestCase
from datetime import date
from books_app import app, db, bcrypt
from books_app.models import Book, Author, User

"""
How to run auth tests:
python -m unittest books_app.auth.tests

How to run all tests:
python -m unittest discover (or just:
python -m unittest; the two are equivalent:
https://docs.python.org/3/library/unittest.html#test-discovery)
"""

#################################################
# Setup
#################################################

def create_books():
    a1 = Author(name='Harper Lee')
    b1 = Book(
        title='To Kill a Mockingbird',
        publish_date=date(1960, 7, 11),
        author=a1
    )
    db.session.add(b1)

    a2 = Author(name='Sylvia Plath')
    b2 = Book(title='The Bell Jar', author=a2)
    db.session.add(b2)
    db.session.commit()

def create_user():
    password_hash = bcrypt.generate_password_hash('password').decode('utf-8')
    user = User(username='me1', password=password_hash)
    db.session.add(user)
    db.session.commit()

#################################################
# Tests
#################################################

class AuthTests(TestCase):
    """Tests for authentication (login & signup)."""
 
    def setUp(self):
        """Executed prior to each test."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

    def test_signup(self):
        # - Make a POST request to /signup, sending a username & password
        post_data = {
            'username': 'newuser',
            'password': 'newpass',
        }
        response = self.app.post('/signup', data=post_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

        # - Check that the user now exists in the database
        created_user = User.query.filter_by(username='newuser').one()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.username, 'newuser')
        self.assertTrue(bcrypt.check_password_hash(created_user.password, 'newpass'))

    def test_signup_existing_user(self):
        # - Create a user
        create_user()

        # - Make a POST request to /signup, sending the same username & password
        post_data = {
            'username': 'me1',
            'password': 'password',
        }
        response = self.app.post('/signup', data=post_data)
        self.assertEqual(response.status_code, 200)

        # - Check that the form is displayed again with an error message
        response_text = response.get_data(as_text=True)
        self.assertIn('That username is taken. Please choose a different one.', response_text)

    def test_login_correct_password(self):
        # - Create a user
        create_user()

        # - Make a POST request to /login, sending the created username & password
        post_data = {
            'username': 'me1',
            'password': 'password',
        }
        response = self.app.post('/login', data=post_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # - Check that the "login" button is not displayed on the homepage
        response_text = response.get_data(as_text=True)
        self.assertIn('Log Out', response_text)
        self.assertNotIn('Log In', response_text)

    def test_login_nonexistent_user(self):
        # - Make a POST request to /login, sending a username & password
        post_data = {
            'username': 'asdfasdf',
            'password': 'asdfasdf'
        }
        response = self.app.post('/login', data=post_data)
        self.assertEqual(response.status_code, 200)

        # - Check that the login form is displayed again, with an appropriate
        #   error message
        response_text = response.get_data(as_text=True)
        self.assertIn('No user with that username. Please try again.', response_text)

    def test_login_incorrect_password(self):
        # - Create a user
        create_user()

        # - Make a POST request to /login, sending the created username &
        #   an incorrect password
        post_data = {
            'username': 'me1',
            'password': 'asdfasdf'
        }
        response = self.app.post('/login', data=post_data)
        self.assertEqual(response.status_code, 200)

        # - Check that the login form is displayed again, with an appropriate
        #   error message
        response_text = response.get_data(as_text=True)
        self.assertIn('Password doesn&#39;t match. Please try again.', response_text)

    def test_logout(self):
        # - Create a user
        create_user()

        # - Log the user in (make a POST request to /login)
        post_data = {
            'username': 'me1',
            'password': 'password'
        }
        response = self.app.post('/login', data=post_data)
        self.assertEqual(response.status_code, 302)

        # - Make a GET request to /logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # - Check that the "login" button appears on the homepage
        response_text = response.get_data(as_text=True)
        self.assertIn('Log In', response_text)
        self.assertNotIn('Log Out', response_text)
