import root_path
root_path.define_sys_path()

import jwt
import app.rest
from config_test import create_db
from app.models import User, db, Friend
from dotenv import load_dotenv
from os import getenv
from flask_login import current_user, login_user
from flask.testing import FlaskClient
from app.models import Group
import unittest
import datetime
from freezegun import freeze_time

load_dotenv()



class LoginTestCase(unittest.TestCase):
   
    def setUp(self):
        self.app = create_db()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.app_test = FlaskClient(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_sucessfull(self):
        """
        Test the successful login functionality.

        Test the functionality of the login feature when the provided credentials are valid.
        This function sends a POST request to the '/login' endpoint with a payload containing 
        the email and password. It then checks if the response status code is 200, indicating 
        a successful login. It also verifies that the logged-in user's email matches the 
        provided email.

        Parameters:
        - self: The instance of the test class.

        Returns:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                payload = {
                    'email': 'email1@example.com',
                    'password': 'password1'
                }
                headers = {
                    'Content-Type': 'application/json',
                    'API-Key': getenv('SECRET_KEY'),
                    'Content-Length': str(len(payload))
                }
                response = self.app_test.post('/login', json=payload, headers=headers)
                self.assertEqual(response.status_code, 200)
                user = User.query.filter_by(email='email1@example.com').first()
                self.assertEqual(user.id, current_user.id)

    def test_generate_recovery_code(self):
        """
        Test the generate_recovery_code endpoint.

        This function tests the behavior of the generate_recovery_code endpoint by making a POST request
        to the '/generate_recovery_code' URL with a valid email payload. It asserts that the response
        status code is 200.

        Parameters:
        - self: The test case instance.

        Returns:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                payload = {
                    'email': 'email1@example.com'
                }
                response = self.app_test.post('/generate_recovery_code', json=payload,
                                              headers={'Content-Type': 'application/json',
                                                       'API-Key': getenv('SECRET_KEY'),
                                                       'Content-Length': len(payload)})
                self.assertEqual(response.status_code, 200)

    def test_login_with_recovery_code(self):
        """
        Test the login with recovery code functionality.
        
        :return: None
        """

        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                recovery_code = user.generate_recovery_token()
                payload = {
                    'recovery_code': recovery_code
                }
                response = self.app_test.post('/login_with_recovery_code',
                                              json=payload,
                                              headers={'Content-Type': 'application/json',
                                                       'API-Key': getenv('SECRET_KEY'), 
                                                       'Content-Length': len(payload)})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(user.id, current_user.id)
    

    def test_login_with_recovery_code_expired(self):
        simulated_current_time = datetime.datetime.now()

        with freeze_time(simulated_current_time):
            with self.app.app_context():
                with self.app.test_request_context():
                    user = User.query.filter_by(email='email1@example.com').first()
                    recovery_code = user.generate_recovery_token()

            simulated_current_time += datetime.timedelta(hours=2)

            with freeze_time(simulated_current_time):
                with self.app.app_context():
                    with self.app.test_request_context():
                        payload = {
                            'recovery_code': recovery_code
                        }
                        response = self.app_test.post('/login_with_recovery_code',
                                                    json=payload,
                                                    headers={'Content-Type': 'application/json',
                                                             'API-Key': getenv('SECRET_KEY'), 
                                                             'Content-Length': len(payload)})
                        self.assertEqual(response.status_code, 401)
            


class SignUpTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_db()
        self.app_test = FlaskClient(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_signup(self):
        """
        Test the signup functionality.

        This function tests the signup functionality of the application. It creates a test context
        and a test request context to simulate a request to the `/signup` endpoint. It sends a POST
        request with a payload containing the user's name, email, and password. The function then
        asserts that the response status code is 201, indicating a successful signup.

        Args:
            self (object): The instance of the test class.

        Returns:
            None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                payload = {
                    'name': 'user5',
                    'email': 'email5@example.com',
                    'password': 'password5'

                }
                response = self.app_test.post('/signup', 
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                  'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)
                                                  })
                self.assertEqual(response.status_code, 201)

    def test_signup_invalid_email(self):
        """
        Test the signup functionality with an invalid email address.
        """
        with self.app.app_context():
            with self.app.test_request_context():
                payload = {
                    'name': 'user5',
                    'email': 'email5',
                    'password': 'password5'
                }
                response = self.app_test.post('/signup',
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                   'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)})
                self.assertEqual(response.status_code, 400)

    def test_signup_duplicate_email(self):
        """
        Test if signing up with a duplicate email returns a 400 status code.
        """
        with self.app.app_context():
            with self.app.test_request_context():
                payload = {
                    'name': 'user5',
                    'email': 'email4@example.com',
                    'password': 'password5'
                }
                response = self.app_test.post('/signup', 
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                   'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)
                                                  })
                self.assertEqual(response.status_code, 400)


class GroupTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_db()

        self.app_test = FlaskClient(self.app)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_group(self):
        """
        Test the create_group function.
        
        This function tests the create_group function in the current class. It sets up the necessary context and request for testing, creates a user object, logs in the user, and prepares a payload with the required data for creating a group. It then sends a POST request to the '/creategroup' endpoint with the payload and headers. Finally, it asserts that the response status code is 201, indicating that the group was successfully created.
        
        Parameters:
            self (TestClassName): The current instance of the test class.
            
        Returns:
            None
        """

        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                login_user(user)
                payload = {
                    'name': 'group2',
                    'creator': current_user.id,
                    'event_date': datetime.datetime.now().__str__(),
                    'min_gift_price': 100,
                    'max_gift_price': 200, 
                    'creator_desired_gift': 'gift1'

                }
                response = self.app_test.post('/creategroup',
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                  'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)
                                                  })
                self.assertEqual(response.status_code, 201)

    def test_su_get_groups(self):
        """
        Test case for the `su_get_groups` function.

        This test case checks if the `su_get_groups` function behaves correctly under certain conditions.
        It sets up a test environment, performs a mock login, and sends a test request to the API endpoint.
        The expected behavior is that the response status code should be 200.

        Parameters:
        - self: The test case object.

        Returns:
        - None
        """
   
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                login_user(user)
                response = self.app_test.get(
                    '/sugetgroups', headers={'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 200)


    def test_su_get_groups_unautorized(self):
        """
        Test the 'su_get_groups_unautorized' function.
        This function tests the behavior of the 'su_get_groups_unautorized' function in the current context.
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email2@example.com').first()
                login_user(user)
                response = self.app_test.get(
                    '/sugetgroups', headers={'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 401)

    def test_su_get_group(self):
        """
        Test the 'su_get_group' endpoint.

        This function tests the 'su_get_group' endpoint of the API. It makes a GET
        request to the endpoint with the given group ID and asserts that the 
        response status code is 200.

        Parameters:
        - self: The test class instance.

        Returns:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                login_user(user)
                group_id = Group.query.filter_by(name='group1').first().id
                response = self.app_test.get('/sugetgroup/{}'.format(group_id), headers={
                                             'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 200)

    def test_su_get_group_unautorized(self):
        """
        This function tests the behavior of the 'su_get_group_unauthorized' API endpoint when an unauthorized user tries to access it.

        Parameters:
            self (TestCase): The current test case.
        
        Returns:
            None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email2@example.com').first()
                login_user(user)
                group_id = Group.query.filter_by(name='group1').first().id
                response = self.app_test.get('/sugetgroup/{}'.format(group_id), headers={
                                             'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 401)

    def test_get_group(self):
        """
        Test the 'get_group' API endpoint.

        This function tests the functionality of the 'get_group' API endpoint. It simulates a user accessing the endpoint
        and verifies that the response status code is 200.

        Parameters:
        - self: The instance of the test case.
        
        Returns:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                login_user(user)

                response = self.app_test.get(
                    '/getcreatorgroups', headers={'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 200)

    def test_get_friends_group(self):
        """
        Test the functionality of the `get_friends_group` endpoint.
        
        This function tests the behavior of the `get_friends_group` endpoint by simulating a request to retrieve the friends group with the given ID. It verifies that the response status code is 200, indicating a successful request.
        
        Parameters:
        - self: The current instance of the test case.
        
        Return Type:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = User.query.filter_by(email='email1@example.com').first()
                login_user(user)
                group = Group.query.filter_by(name='group1').first()
                response = self.app_test.get('/getfriendsgroup/{}'.format(group.id), headers={
                                             'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 200)

    def test_get_friends_group_unautorized(self):
        """
        Test the get_friends_group_unauthorized function.

        This function tests the functionality of the get_friends_group_unauthorized
        endpoint. It ensures that the endpoint returns a 401 status code when an
        unauthorized user tries to access the group's friends.

        Parameters:
        - self: The current instance of the test class.

        Returns:
        - None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user5 = User('user5', 'email5@example.com', 'password5')
                db.session.add(user5)
                db.session.commit()
                login_user(user5)
                group = Group.query.filter_by(name='group1').first()
                response = self.app_test.get('/getfriendsgroup/{}'.format(group.id), headers={
                                             'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})
                self.assertEqual(response.status_code, 401)

    def test_perfect_drawn_group(self):
        """
        Test the perfect drawn group functionality.

        This function tests the perfect drawn group functionality by simulating a request to the '/perfectdrawngroup' endpoint.
        It ensures that the response status code is 200 and that the 'drawn' attribute of the group is set to True.
        It also checks that all the friends associated with the group have a non-null 'friend_id'.

        Parameters:
        - self: The current instance of the test case.

        Returns:
        None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = db.session.query(User).filter_by(
                    email='email1@example.com').first()
                login_user(user)
                group = Group.query.filter_by(name='group1').first()
                payload = {
                    'group_id': group.id,
                }
                response = self.app_test.post('/perfectdrawngroup',
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                  'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)
                                                  })

                self.assertEqual(response.status_code, 200)
                self.assertTrue(group.drawn)
                self.assertTrue(all([friend.friend_id for friend in group.friends]))

    def test_imperfect_drawn_group(self):
        """
        Test the imperfect drawn group functionality.

        This function tests the functionality of the '/imperfectdrawngroup' API endpoint.
        It ensures that a group can be marked as drawn and that all friends in the group
        have a friend_id associated with them.

        Parameters:
        - self: The current instance of the test class.

        Returns:
        None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = db.session.query(User).filter_by(
                    email='email1@example.com').first()
                login_user(user)
                group = Group.query.filter_by(name='group1').first()
                payload = {
                    'group_id': group.id
                }
                response = self.app_test.post('/imperfectdrawngroup',
                                              json=payload,
                                              headers={
                                                  'Content-Type': 'application/json',
                                                  'API-Key': getenv('SECRET_KEY'),
                                                  'Content-Length': len(payload)
                                                  })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(group.drawn)
                self.assertTrue(
                    all([friend.friend_id for friend in group.friends]))

    def test_getmyfriend(self):
        """
        Test the getmyfriend API endpoint.

        The function sends a GET request to the '/getmyfriend/{group_id}' endpoint
        with the necessary headers and parameters. It asserts that the response
        status code is 200.

        Parameters:
        - self: The current test case object.

        Returns:
        None
        """
        with self.app.app_context():
            with self.app.test_request_context():
                user = db.session.query(User).filter_by(
                    email='email1@example.com').first()
                login_user(user)
                group: Group = Group.query.filter_by(name='group1').first()
                group.perfect_drawn()
            
                response = self.app_test.get('/getmyfriend/{}'.format(group.id),
                                             headers={'Content-Type': 'application/json', 'API-Key': getenv('SECRET_KEY')})

                self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
