
import root_path
root_path.define_sys_path()

from app.utils import test_headers
import jwt
import app.rest as rest
from config_test import create_db
from app.models import User, db, Friend
from dotenv import load_dotenv
from os import getenv

from flask.testing import FlaskClient
from app.models import Group
import unittest
import datetime
from freezegun import freeze_time
import uuid

load_dotenv()


def setup(testcase):
    """
    Sets up the necessary context and objects for a test case.
    
    Args:
        testcase: The test case object.
    
    Returns:
        None
    """
    testcase.app = create_db()
    testcase.app_context = testcase.app.app_context()
    testcase.app_context.push()
    testcase.request_context = testcase.app.test_request_context()
    testcase.request_context.push()
    testcase.app_test = FlaskClient(testcase.app)
    
    

def teardown(testcase):
    """
    A function to tear down the testcase by popping the app context and request context.

    Args:
        testcase: The testcase object.

    Returns:
        None
    """
    testcase.app_context.pop()
    testcase.request_context.pop()




class LoginTestCase(unittest.TestCase):
   
    def setUp(self):
        setup(self)
       

    def tearDown(self):
        teardown(self)
       

    def test_login_sucessful(self):
        """
        Test the successful login functionality.

        This function sends a POST request to the '/login' endpoint with a valid email and password.
        It then checks if the response status code is 200 and if the access token in the response
        matches the access token generated for the user with the given email.

        Parameters:
            self (object): The current instance of the test class.

        Returns:
            None
        """
        with freeze_time('2019-12-01 01:01:01'):
            payload = {
                'email': 'email1@example.com',
                'password': 'password1'
            }
    
            headers = test_headers(payload)
            response = self.app_test.post('/login', json=payload, headers=headers)
            user:User = User.query.filter_by(email='email1@example.com').first()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['access_token'], user.generate_access_token())

    def test_login_failed(self):
        payload = {
            'email': 'email1@example.com',
            'password': 'wrongpassword'
        }
        headers = test_headers(payload)
        response = self.app_test.post('/login', json=payload, headers=headers)
        self.assertEqual(response.status_code, 401)

class SignUpTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
       

    def tearDown(self):
        teardown(self)
   
    def test_successful(self):

        with freeze_time('2019-12-01 01:01:01'):
           payload = {
               'name': 'test',
               'email': 'test@example.com',
               'password': 'test'
           }
           headers = test_headers(payload)
           response = self.app_test.post('/signup', json=payload, headers=headers)
           payload['exp'] = datetime.datetime.now() + datetime.timedelta(days=1)
           test_token = jwt.encode(payload, rest.SECRET_KEY, algorithm='HS256')
           self.assertEqual(response.status_code, 201)
           self.assertEqual(response.json['access_token'], test_token)
    
    def test_key_error(self):
        payload = {
            'name': 'test',
            'email': 'test@example.com'
        }
        headers = test_headers(payload)
        response = self.app_test.post('/signup', json=payload, headers=headers)
        self.assertEqual(response.json['message'],'Invalid input')
    
    def test_not_found_email(self):
        payload = {
            'name': 'test',
            'email': 'email1@example.com',
            'password': 'test'
        }
        headers = test_headers(payload)
        response = self.app_test.post('/signup', json=payload, headers=headers)
        self.assertEqual(response.json['message'],'User already exists')

    def test_invalid_email(self):
        payload = {
            'name': 'test',
            'email': 'test',
            'password': 'test'
        }
        headers = test_headers(payload)
        response = self.app_test.post('/signup', json=payload, headers=headers)
        self.assertEqual(response.json['message'],'Invalid email')

class ValidateEmailTestCase(unittest.TestCase):   
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
    
    def test_validate_email_sucessful(self):
        with freeze_time('2019-12-01 01:01:01'):
            data = {
                'name': 'test',
                'email': 'test@example.com',
                'password': 'test', 
                'exp': (datetime.datetime.now() + datetime.timedelta(days=1)).timestamp()
            }
            payload = {
                'email_validation_token': jwt.encode(data, rest.SECRET_KEY, algorithm='HS256')
            }
            headers = test_headers(payload)
            email_validation_token = payload['email_validation_token']
            response = self.app_test.get(f'/validate_email/{email_validation_token}', headers=headers)
            self.assertEqual(response.status_code, 201)
            user = User.query.filter_by(email='test@example.com').first()
            self.assertIsNotNone(user)
    
    def test_validate_email_with_expired_token(self):
        with freeze_time('2019-12-01 01:01:01'):
            data = {
                'name': 'test',
                'email': 'test@example.com',
                'password': 'test', 
                'exp': (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
            }
            payload = {
                'email_validation_token': jwt.encode(data, rest.SECRET_KEY, algorithm='HS256')
            }
            headers = test_headers(payload)
            email_validation_token = payload['email_validation_token']
            response = self.app_test.get(f'/validate_email/{email_validation_token}', headers=headers)
            self.assertEqual(response.status_code, 401)

class GenerateRecoveryCodeTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
       

    def tearDown(self):
        teardown(self)
    
    def test_generate_recovery_code(self):
        user = User.query.filter_by(email='email1@example.com').first()
        email = user.email

        with freeze_time('2019-12-01 01:01:01'):
            headers = test_headers()
            response = self.app_test.get(f'/generate_recovery_code/{email}', headers=headers)
            self.assertEqual(response.status_code, 200)

class LoginWithRecoveryCodeTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
      
    def test_login_with_valid_recovery_token(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        with freeze_time('2019-12-01 01:01:01'):
            recovery_code = user.generate_recovery_token()
            headers = test_headers()
            response = self.app_test.get(f'/login_with_recovery_code/{recovery_code}', headers=headers)
            self.assertAlmostEqual(response.status_code, 200)
    
    def test_login_with_invalid_id_recovery_token(self):
        fake_user = User(name='fake_user', email='fake_user@example.com', password='fake_user')
        fake_user.id = uuid.uuid4().hex
        with freeze_time('2019-12-01 01:01:01'):
            fake_token = fake_user.generate_recovery_token()
            headers = test_headers()
            response = self.app_test.get(f'/login_with_recovery_code/{fake_token}', headers=headers)
            self.assertAlmostEqual(response.status_code, 500)
        
    def test_login_with_expired_recovery_token(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        with freeze_time('2019-12-01 01:01:01'):
            recovery_code = user.generate_recovery_token()
            headers = test_headers()
        with freeze_time('2019-12-03 01:01:01'):
            response = self.app_test.get(f'/login_with_recovery_code/{recovery_code}', headers=headers)
        self.assertAlmostEqual(response.status_code, 401)
    

    
    

class CreateGroupTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
       

    def tearDown(self):
        teardown(self)
    
    def test_create_group(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        with freeze_time('2019-12-01 01:01:01'):
            payload = {
                'description': 'test',
                'creator_id': user.id,
                'event_date': (datetime.datetime.now()+datetime.timedelta(days=20)).strftime('%Y-%m-%d'),
                'min_gift_price': 10,
                'max_gift_price': 20, 
                'creator_desired_gift': 'gift'
            }
            headers = test_headers(payload=payload,authorization=user.generate_access_token())
            response = self.app_test.post('/create_group', json=payload, headers=headers)

    def test_create_group_invalid_gift_prices(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        with freeze_time('2019-12-01 01:01:01'):
            payload = {
                'description': 'test',
                'creator_id': user.id,
                'event_date': (datetime.datetime.now()+datetime.timedelta(days=20)).strftime('%Y-%m-%d'),
                'min_gift_price': 10,
                'max_gift_price': 0, 
                'creator_desired_gift': 'gift'
            }
            headers = test_headers(payload=payload,authorization=user.generate_access_token())
            response = self.app_test.post('/create_group', json=payload, headers=headers)
            self.assertEqual(response.status_code, 412)

class GetFriendsGroupTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)

    def test_get_friends_group(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        response = self.app_test.get(f'/getfriendsgroup/{group.id}', headers=test_headers(authorization=user.generate_access_token()))
        self.assertEqual(response.status_code, 200)

class PerfectDrawnTestCase(unittest.TestCase):
    def setUp(self):
        
        setup(self)
    def tearDown(self):
        teardown(self)
    
    

    def test_perfect_drawn(self):
        user:User = User.query.filter_by(email='email1@example.com').first()

        group:Group = Group.query.filter_by(description='group1').first()
        self.assertEqual(group.drawn, 'NO')
        payload = {
            'group_id': group.id
        }
        
        response = self.app_test.put('/perfectdrawngroup', json=payload, headers=test_headers(authorization=user.generate_access_token()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(group.drawn , 'PERFECT')
    
    
    def test_perfect_draw_without_admin(self):
        user = User.query.filter_by(email='email2@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        self.assertEqual(group.drawn, 'NO')
        payload = {
            'group_id': group.id
        }
        response = self.app_test.put('/perfectdrawngroup', json=payload, headers=test_headers(authorization=user.generate_access_token()))
        self.assertEqual(response.status_code, 401)


class ImperfectDrawnTestCase(unittest.TestCase):
    def setUp(self):
       
        setup(self)
    def tearDown(self):
        teardown(self)
    def test_imperfect_drawn(self):
        user:User = User.query.filter_by(email='email1@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        self.assertEqual(group.drawn, 'NO')
        payload = {
            'group_id': group.id
        }
        response = self.app_test.put('/imperfectdrawngroup', 
                                     json=payload, 
                                     headers=test_headers(authorization=user.generate_access_token()))
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(group.drawn , 'IMPERFECT')

    def test_imperfect_draw_without_admin(self):
        user = User.query.filter_by(email='email2@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        self.assertEqual(group.drawn, 'NO')
        payload = {
            'group_id': group.id
        }
        response = self.app_test.put('/imperfectdrawngroup', 
                                     json=payload, 
                                     headers=test_headers(authorization=user.generate_access_token()))
        self.assertEqual(response.status_code, 401)


class SugetGroupsTestCase(unittest.TestCase):
    
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
    
    def test_sugetgroups(self):
        user = User.query.filter_by(email='email1@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get('/sugetgroups', headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_sugetgroups_without_super_user(self):
        user = User.query.filter_by(email='email2@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get('/sugetgroups', headers=headers)
        self.assertEqual(response.status_code, 401)

class SugetUsersTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
    
    def test_sugetusers(self):
        user = User.query.filter_by(email='email1@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get('/sugetusers', headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_sugetusers_without_super_user(self):
        user = User.query.filter_by(email='email2@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get('/sugetusers', headers=headers)
        self.assertEqual(response.status_code, 401)

class SugetGroupTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
    
    def test_sugetgroup(self):
        user = User.query.filter_by(email='email1@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get(f'/sugetgroup/{group.id}', headers=headers)
        self.assertEqual(response.status_code, 200)
    def test_sugetgroup_without_super_user(self):
        user = User.query.filter_by(email='email2@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
       
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get(f'/sugetgroup/{group.id}', headers=headers)
        self.assertEqual(response.status_code, 401)

class UserTestCase(unittest.TestCase):

    def setUp(self):
        #I do no want to re-create the db for each test, so I call a function to re-create the db
        setup(self)
    def tearDown(self):
        teardown(self)
    
    def test_get_group_created_by(self):
        user = User.query.filter_by(email='email1@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        response = self.app_test.get('/getgroupcreatedby/', headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_get_my_friend(self):
        user = User.query.filter_by(email='email1@example.com').first()
        headers = test_headers(authorization=user.generate_access_token())
        group = Group.query.filter_by(description='group1').first()
        group.perfect_drawn()
        response = self.app_test.get(f'/getmyfriend/{group.id}', headers=headers)
        self.assertEqual(response.status_code, 200)
    
class KickGroupTestCase(unittest.TestCase):
    def setUp(self):
        setup(self)
    def tearDown(self):
        teardown(self)
    def test_kick_group_before_draw(self):
        
        admin = User.query.filter_by(email='email1@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        user = User.query.filter_by(email='email2@example.com').first()     
        token = admin.generate_access_token()   
        friend = Friend.query.filter_by(user_id=user.id, group_id=group.id).first()
        response = self.app_test.delete(f'/kickoutgroup/{group.id}/{user.id}', 
                                        headers=test_headers(authorization=token))
        group = Group.query.filter_by(id=group.id).first()
        self.assertEqual(response.status_code, 200)

        
        self.assertEqual(group.drawn, 'NO')
        self.assertEqual(len(group.friends), 3)  
        expected_response = {'message': 'User Kicked'}
        self.assertEqual(response.json, expected_response)
    
    def test_kick_group_after_draw(self):
        
        admin = User.query.filter_by(email='email1@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        group.imperfect_drawn()
        user = User.query.filter_by(email='email2@example.com').first()     
        token = admin.generate_access_token()   
        friend = Friend.query.filter_by(user_id=user.id, group_id=group.id).first()
        response = self.app_test.delete(f'/kickoutgroup/{group.id}/{user.id}', 
                                        headers=test_headers(authorization=token))
        group = Group.query.filter_by(id=group.id).first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(group.drawn, 'NO')
        expected_response = {'message': 'User Kicked, Another Draw Must Be Made'}
        self.assertEqual(response.json, expected_response)
    def test_no_admin_try_kick(self):
        fake_admin = User.query.filter_by(email='email2@example.com').first()
        group:Group = Group.query.filter_by(description='group1').first()
        user = User.query.filter_by(email='email2@example.com').first()
        token = fake_admin.generate_access_token()
        response = self.app_test.delete(f'/kickoutgroup/{group.id}/{user.id}',
                                        headers=test_headers(authorization=token))
        self.assertEqual(response.status_code, 401)
        
       

        

    
    
    


if __name__ == '__main__':
    unittest.main()
    

