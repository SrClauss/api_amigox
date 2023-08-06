
from flask_restful import request, Resource
from dotenv import load_dotenv
from os import getenv
from app.models import User, Group, Friend
import app.config as app_config
import re
from sqlalchemy.exc import  DataError
from functools import wraps
import jwt
import datetime
from app.utils import send_confirmation_email, send_recovery_email
load_dotenv()


db, api = app_config.db, app_config.api

API_KEY = getenv('API_KEY')
SECRET_KEY = getenv('SECRET_KEY')



def required_api_key(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if "Api_Key" not in request.headers:
            return {'message': 'Api_Key header not found'}, 401
        if request.headers['Api_Key'] != API_KEY:
            return {'message': 'Api_Key does not match'}, 401
        return f(*args, **kwargs)

def required_access_token(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        """
        Decorator function to handle token authorization.

        Parameters:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Tuple: A tuple containing the response message and status code.
        """
        if 'Authorization' not in request.headers:
            return {'message': 'Authorization header not found'}, 401
        token = request.headers['Authorization'].removeprefix('Bearer ')
    
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return {'message': 'Token expired'}, 401
       
        if payload.get('exp') < int(datetime.datetime.now().timestamp()):
            return {'message': 'Token expired'}, 401
        
        user = User.query.filter_by(id=payload.get('id')).first()

        return f(*args, **kwargs, user=user)
    

    return decorator

def generate_logs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        import logging
        logging.basicConfig(filemode='api.log', level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        #logger.debug('Request Headers: %s', request.headers)
        logger.debug('Request Body: %s', request.get_json())
        return func(*args, **kwargs)
    return wrapper

#TODO An decorator with verify if the user logged is

class Login(Resource):
 
    
    def post(self):

        '''
        Handles a POST request to log in the user.

        Parameters:
            None
        Example Payload:
            {
                "email": "email1@example.com",
                "password": "password1"
            }
        returns:
            - If email not is in the database, returns a dictionary with the message 'User does not exist' and a status code of 404.
            - If password is incorrect, returns a dictionary with the message 'Invalid password' and a status code of 401.
            - If the user's password is correct, return a dictionary with the acess token and a status code of 200.

        '''
        user = User.query.filter_by(email=request.json.get('email')).first()
        if user:
            if user.check_password(request.json.get('password')):
                
                token = user.generate_access_token()
                return {'access_token': token}, 200
            
        return {'message': 'Invalid login'}, 401
api.add_resource(Login, '/login')

class SignUp(Resource):
   
    def post(self):
        """
        Handles a POST request to create a new user and generate a token for email verification
        
        Parameters:
            None
        
        Returns:
            If the request is invalid, returns a dictionary with a 'message' key and a 400 status code.
            If the user already exists, returns a dictionary with a 'message' key and a 400 status code.
            If the email is invalid, returns a dictionary with a 'message' key and a 400 status code.
            If the request is valid, returns a dictionary with a 'message' key, a 201 status code, and sends an email.
        """
      
        data = request.get_json()

 
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        social_media = data.get('social_media')
 
        if not name or not email or not password:
            return {'message': 'Invalid input'}, 400

        if User.query.filter_by(email=email).first():
            return {'message': 'User already exists'}, 400

        if not re.match(r'^[a-z0-9]+@[a-z]+\.[a-z]{2,3}$', email):
            return {'message': 'Invalid email'}, 400

        payload = {
            'name': name,
            'email': email,
            'password': password,
            'social_media': social_media,
            'exp': datetime.datetime.now() + datetime.timedelta(days=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        send_confirmation_email(email, token)
        
        
        return {'message': 'Verification email sent', 'access_token': token}, 201
        
api.add_resource(SignUp, '/signup')


class ValidateEmail(Resource):
    
    
    def get(self, email_validation_token):
        """
        This function handles a GET request to validate an email.
        It expects an email validation token as part of the URL path.
        The token is decoded using the SECRET_KEY and checked for expiration.
        If the token is expired, a response with a 401 status code and a 'Token expired' message is returned.
        If the token is valid, a new User object is created using the decoded payload fields.
        The user object is then added to the database session and committed.
        If any error occurs during the database operation, a response with a 500 status code and an 'Error creating user' message is returned.
        If the user is successfully created, a response with a 201 status code and a 'User created' message is returned.

        Parameters:
        - email_validation_token: The email validation token obtained from the URL path.

        Returns:
        A dictionary containing the response message and the HTTP status code.
        """
        try:
            payload = jwt.decode(email_validation_token, SECRET_KEY, algorithms=['HS256'])
        except jwt.exceptions.ExpiredSignatureError:
            return {'message': 'Token expired'}, 401
        
       
        try:
            user = User(payload.get('name'), payload.get('email'), payload.get('password'))
            db.session.add(user)
            db.session.commit()
            access_token = user.generate_access_token()
        except DataError:
            return {'message': 'Error creating user'}, 500
        return {'message': 'User created', 'access_token': access_token}, 201

api.add_resource(ValidateEmail, '/validate_email/<email_validation_token>')




class GenerateRecoveryCode(Resource):
    
    
    def get(self, email):
        """
        Retrieves the recovery code for a user and sends it to their email address.

        Parameters:
            email (str): The email address of the user.

        Returns:
            dict: A dictionary containing the message 'Recovery code sent'.
                  This indicates that the recovery code was successfully sent.
            int: The HTTP status code 200, indicating a successful request.

        Raises:
            404: If the user with the given email address does not exist.
        """
        user: User = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'User does not exist'}, 404
        recovery_token = user.generate_recovery_token()
        send_recovery_email(email, recovery_token)
        return {'message': 'Recovery code sent'}, 200
    # TODO: Implement a captcha
api.add_resource(GenerateRecoveryCode, '/generate_recovery_code/<string:email>')




class LoginWithRecoveryCode(Resource):
 
    
    
    def get(self, recovery_code):
        """
        Retrieves the user's access token using a recovery code.

        Parameters:
            recovery_code (str): The recovery code generated for the user.

        Returns:
            dict, int: A dictionary containing the user's access token and HTTP status code.
        """
    
        try:
            payload = jwt.decode(recovery_code, SECRET_KEY, algorithms=['HS256'])
        except jwt.exceptions.ExpiredSignatureError:
            return {'message': 'Token expired'}, 401
        user = User.query.filter_by(id=payload.get('id')).first()
        if not user:
            return {'message': 'An error occurred'}, 500
        access_token = user.generate_access_token()
        return {'access_token': access_token}, 200
    

api.add_resource(LoginWithRecoveryCode, '/login_with_recovery_code/<string:recovery_code>')



class CreateGroup(Resource):
    
    
    
    @required_access_token
    def post(self, user: User):
        """
        Creates a new group and adds the current user as the creator and a member of the group.

        Args:
            user (User): The user object representing the current user.
        Example Payload:
            {
                "name": "New Group",
                "event_date": "2020-01-01",
                "min_gift_price": 10,
                "max_gift_price": 100
                
            }

        Returns:
            dict: A dictionary containing the message 'Group created'.
            int: The HTTP status code 201 indicating a successful creation.
        """

        data = request.get_json()
        description = data.get('description')
        creator = user.id
        event_date = datetime.datetime.strptime(data.get('event_date'), '%Y-%m-%d')
        min_gift_price = data.get('min_gift_price')
        max_gift_price = data.get('max_gift_price')
        creator_desired_gift = data.get('creator_desired_gift')
        if min_gift_price > max_gift_price:
            return {'message': 'min_gift_price must be less than max_gift_price'}, 412
        if not description or not event_date or not min_gift_price or not max_gift_price:
            return {'message': 'Invalid input'}, 400
        
        group: Group = Group(description, creator, event_date, min_gift_price, max_gift_price)

        db.session.add(group)
        db.session.commit()
        db.session.add(Friend(user.id, group.id, creator_desired_gift))
        db.session.commit()
        return {'message': 'Group created'}, 201
    
       

api.add_resource(CreateGroup, '/create_group')
class SuGetUsers(Resource):
    

    @required_access_token
    def get(self, user: User):
        """
        A function that retrieves a list of users, this route requires the current user to be a superuser.

        Returns:
            - If the current user is a superuser, a serialized list of all users.
            - If the current user is not a superuser, a dictionary with a message indicating unauthorized access and a status code of 401.
        """
        if user.is_superuser:
            serialized_users = [user.serialize() for user in User.query.all()]
            return  serialized_users, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(SuGetUsers, '/sugetusers')


class SuGetGroups(Resource):
    
    
    @required_access_token
    def get(self, user: User):
        """
        A function that retrieves a list of groups, this route requires the current user to be a superuser.

        Returns:
            - If the current user is a superuser, a serialized list of all groups.
            - If the current user is not a superuser, a dictionary with a message indicating unauthorized access and a status code of 401.
        """
     
        if user.is_superuser:
            serialized_groups = [group.serialize() for group in Group.query.all()]
            return serialized_groups, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(SuGetGroups, '/sugetgroups')

class SuGetGroup(Resource):
    
    
    
    @required_access_token
    def get(self, user, group_id):
        """
        Retrieves a serialized group object based if the current user is a superuser.

        Parameters:
            group_id (int): The ID of the group to retrieve.

        Returns:
            dict: A serialized group object if the current user is a superuser.
            dict: {'message': 'Unauthorized'} with status code 401 if the current user is not a superuser.
        """
        
        if user.is_superuser:
            
            serialized_group = Group.query.filter_by(id=group_id).first().su_serialize()
            return serialized_group
        return {'message': 'Unauthorized'}, 401

api.add_resource(SuGetGroup, '/sugetgroup/<string:group_id>')

class GetGroup(Resource):
    
    
    @required_access_token
    def get(self, user, group_id):
        """
        Retrieves and serializes a group object based on the specified group ID.

        Args:
            user (User): The user object making the request.
            group_id (int): The ID of the group to retrieve.

        Returns:
            tuple: A tuple containing the serialized group object and the HTTP status code 200.
        """

        group = Group.query.filter_by(id=group_id).first()
        serialized_group = group.serialize()
        
        return {'serialized_group': serialized_group}, 200


class GetGroupCreatedBy(Resource):
    
    
    @required_access_token
    
    def get(self, user):
        """
        Retrieves all groups created by the current user.

        Returns:
            list: A list of serialized group objects representing the groups created by the current user. If no groups are found, an empty list is returned.
        """

        groups = Group.query.filter_by(creator=user.id).all()
        serialized_groups = [group.serialize() for group in groups]
        return serialized_groups if serialized_groups else []
api.add_resource(GetGroupCreatedBy, '/getgroupcreatedby')

class GetFriendsGroup(Resource):
    
    
    @required_access_token
    
    def get(self, user, group_id):
        """
        Get the list of friends in a group.

        Parameters:
            group_id (int): The ID of the group.

        Returns:
            list: A list of serialized friend objects.

        Raises:
            dict: A dictionary with an 'message' key and a status code of 401 if the user is not authorized.
        """
        
        group = Group.query.filter_by(id=group_id).first()
        friend_user = [friend for friend in group.friends if friend.user_id == user.id]
        if friend_user:
            friends = [friend.serialize() for friend in group.friends]
            return friends
        return {'message': 'Unauthorized'}, 401
api.add_resource(GetFriendsGroup, '/getfriendsgroup/<string:group_id>')

class PerfectDrawnGroup(Resource):
    
    
    @required_access_token

    
    
    def put(self, user):
        
        group:Group = Group.query.filter_by(id=request.json.get('group_id')).first()
        try:

            friend_user = [friend for friend in group.friends if friend.user_id == user.id]
        except AttributeError:
            return {'message': 'An error occurred'}, 500
        
        if friend_user:
            if friend_user[0].is_admin:
                group.perfect_drawn()
                return {'message': 'Perfect Drawn completed'}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(PerfectDrawnGroup, '/perfectdrawngroup')

class KickOutGroup(Resource):
    
    
    @required_access_token
    def delete(self, group_id, kicked_user_id, user):
        """
        A function that handles the DELETE request for kicking out a friend from a group.

        Args:
            user (User): The user object representing the authenticated user (sent in the request header as authorization).
            group (Group): The group object representing the group to be kicked out.
            friend (Friend): The friend object representing the friend to be kicked out.
        Returns:
            dict: A dictionary containing the response message and status code.
        """

        group:Group = Group.query.filter_by(id=group_id).first()
        kicker_friend = Friend.query.filter_by(user_id=user.id, group_id=group_id).first()
        kicked_friend = Friend.query.filter_by(user_id=kicked_user_id, group_id=group_id).first()
        if kicker_friend and kicker_friend.is_admin and kicked_friend:
            if group.drawn == "PERFECT" or group.drawn == "IMPERFECT":
                for friend in group.friends:
                    friend.friend_id = None
                group.kick_out(kicked_user_id)
                group.drawn = "NO"
                db.session.commit()
                return {'message': 'User Kicked, Another Draw Must Be Made'}, 200
            else:
                group.kick_out(kicked_user_id)
                return {'message': 'User Kicked'}, 200
        return {'message': 'Unauthorized'}, 401
    

              

api.add_resource(KickOutGroup, '/kickoutgroup/<string:group_id>/<string:kicked_user_id>')



class ImperfectDrawnGroup(Resource):
    
    
    @required_access_token

    
    
    def put(self, user):
        """
        A function that handles the PUT request for updating a user's group.

        Args:
            user (User): The user object representing the authenticated user.

        Returns:
            dict: A dictionary containing the response message and status code.
        """
        
        
       
        group = Group.query.filter_by(id=request.get_json().get('group_id')).first()
        try:
            friend_user = [friend for friend in group.friends if friend.user_id == user.id]
        except AttributeError:
            return {'message': 'An error occurred'}, 500
        if friend_user:
            if friend_user[0].is_admin:
                group.imperfect_drawn()
                return {'message': 'Imperfect Drawn completed'}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(ImperfectDrawnGroup, '/imperfectdrawngroup')
            

class GetMyFriend(Resource):
    
    
    
    @required_access_token
    def get(self, user, group_id):
        """
        Retrieves information about a friend in a group.

        Args:
            group_id (int): The ID of the group.

        Returns:
            dict: A dictionary containing the friend's name, ID, and desired gift.
            int: The HTTP status code 200 if the request is successful.
            dict: A dictionary containing an error message if the request is unauthorized.
            int: The HTTP status code 401 if the request is unauthorized.
        """
     
        group = Group.query.filter_by(id=group_id).first()
        friend_user = [friend for friend in group.friends if friend.user_id == user.id]
        
        if friend_user:
            return{'friend_name': friend_user[0].serialize()['friend_name'], 
                   'friend_id': friend_user[0].friend_id, 
                   'friend_gift':Friend.query.filter_by(user_id=friend_user[0].friend_id).first().gift_desired}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(GetMyFriend, '/getmyfriend/<string:group_id>')

class GetCurrentUser(Resource):
    @required_access_token
    def get(self, user):
        """
        Retrieves information about the current user.

        args:
            user (User): The user object representing the authenticated user.
        returns:
            dict: A dictionary containing the user's name, ID, and email.
            int: The HTTP status code 200 if the request is successful.
            dict: A dictionary containing an error message if the request is unauthorized.
            int: The HTTP status code 401 if the request is unauthorized.
        """

        return user.serialize(), 200

api.add_resource(GetCurrentUser, '/user')


class GetJoinedGroups(Resource):
    @required_access_token
    def get(self, user):
        """
        Retrieves all groups the current user is a member of.

        args:
            user (User): The user object representing the authenticated user.
        returns:
            list: A list of serialized group objects representing the groups the current user is a member of.
            int: The HTTP status code 200 if the request is successful.
            dict: A dictionary containing an error message if the request is unauthorized.
            int: The HTTP status code 401 if the request is unauthorized.
        """

        friends = Friend.query.filter_by(user_id=user.id).all()
        if friends:
            groups = []
            for friend in friends:
                groups.append(Group.query.get(friend.group_id))

            return [group.serialize() for group in groups], 200
        
api.add_resource(GetJoinedGroups, '/getjoinedgroups')

