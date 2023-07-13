
from flask_restful import request, Resource, Api
from dotenv import load_dotenv
from os import getenv
from flask_login import LoginManager, login_user, current_user
from app.models import User, app, db, Group, Friend
import re
from sqlalchemy.exc import IntegrityError, DataError
from functools import wraps
import jwt


login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)

def login_required(func):
    """
    Decorator that checks if the user is authenticated before executing the function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.

    Raises:
        None.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
       if current_user.is_authenticated:
           return func(*args, **kwargs)
       else:
           return {'message': 'Unauthorized'}, 401
    return wrapper

def validate_headers(func):
    """
    This function is a wrapper that validates the request headers and API key before executing the provided function.

    Parameters:
        *args: Positional arguments passed to the wrapped function.
        **kwargs: Keyword arguments passed to the wrapped function.

    Returns:
        The return value of the wrapped function.

    Raises:
        Returns a dictionary with the following keys if the request headers or API key are invalid:
            - {'message': 'Invalid Content-Type header'} if the 'Content-Type' header is missing or not 'application/json'.
            - {'message': 'Invalid API-Key header'} if the 'API-Key' header does not match the expected API key.
            - Returns the wrapped function's return value if the headers and API key are valid.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
      
        if 'Content-Type' not in request.headers or request.headers['Content-Type'] != 'application/json':
            return {'message': 'Invalid Content-Type header'}, 400

        api_key = request.headers.get('API-Key')
        expected_api_key = getenv("SECRET_KEY")

        if api_key != expected_api_key:
            return {'message': 'Invalid API-Key header'}, 401

        return func(*args, **kwargs)

    return wrapper

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database based on the given user ID.

    Parameters:
        user_id (int): The ID of the user to load.

    Returns:
        User: The user object corresponding to the given user ID.
    """
    return User.query.get(user_id)



class Login(Resource):
    @validate_headers
    def post(self):
        """
        Handles a POST request to log in the user.

        Validates the headers of the request using the `validate_headers` decorator.

        Parameters:
            None

        Example Payload:
            {
                "email": "email1@example.com",
                "password": "password1"
            }

        Returns:
            If the user's password is correct, it logs the user in and returns a dictionary with the message 'Login successful' and the HTTP status code 200.
            If the user's password is incorrect, it returns a dictionary with the message 'Login failed' and the HTTP status code 401.
        """
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()

        if user.check_password(data.get('password')):
            login_user(user)
            return {'message': 'Login successful'}, 200

        return {'message': 'Login failed'}, 401
api.add_resource(Login, '/login')

class SignUp(Resource):
    @validate_headers
    def post(self):
        """
        Create a new user with the provided information.
        
        Parameters:
            None
        
        Example Payload:
            {
                "name": "John Doe",
                "email": "email1@example.com",
                "password": "password1"
            }

        Returns:
            - If successful, returns a dictionary with the message 'User created' and a status code of 201.
            - If the user with the provided email already exists, returns a dictionary with the message 'Email already exists' and a status code of 500.
            - If there is an error creating the user, returns a dictionary with the message 'Error creating user' and a status code of 500.

        Raises:
            - KeyError: If the required fields 'name', 'email', or 'password' are not provided in the request body.
            - DataError: If there is an error committing the user to the database.

        Notes:
            - This function requires the 'validate_headers' decorator to be applied to it.
            - The email format is validated using a regex pattern.
        """
        data = request.get_json()

        try:
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
        except KeyError:
            return {'message': 'Invalid input'}, 400

        if not name or not email or not password:
            return {'message': 'Invalid input'}, 400

        if User.query.filter_by(email=email).first():
            return {'message': 'User already exists'}, 400

        if not re.match(r'^[a-z0-9]+@[a-z]+\.[a-z]{2,3}$', email):
            return {'message': 'Invalid email'}, 400

        try:
            with db.session.begin_nested():
                user = User(name, email, password)
                db.session.add(user)
                db.session.commit()
                return {'message': 'User created'}, 201
            
        except IntegrityError:
            return {'message': 'Email already exists'}, 500
        except DataError:
            return {'message': 'Error creating user'}, 500
api.add_resource(SignUp, '/signup')

class ExchangePassword(Resource):
    @validate_headers
    @login_required
    def post(self):
        """
        Handles the HTTP POST request to change the user's password.

        Parameters:
            None
        
        Example Payload:
            {
                "old_password": "password1",
                "new_password": "password2"

            }

        Returns:
            A dictionary containing the response message and the HTTP status code.
    	"""
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        user = current_user
        if not user.check_password(old_password):
            return {'message': 'Invalid password'}, 401
        user.password = new_password
        db.session.commit()
        return {'message': 'Password changed'}, 200
api.add_resource(ExchangePassword, '/change_password')

class GenerateRecoveryCode(Resource):
    @validate_headers
    def post(self):
        """
        This function is a POST endpoint that handles the request to generate a recovery token for a given email.
        
        Parameters:
            None
        Example Payload:
            {
                "email": "email1@example.com"

            }
            
        Returns:
            If the email is not found in the User table, it returns a JSON response with a 'message' key set to 'email not found' and a status code of 404.
            If the email is found, it generates a recovery token for the user and returns a JSON response with a 'recovery_code' key set to the generated token and a status code of 200.
        """

        
        email = request.get_json().get('email')
        user:User = User.query.filter_by(email=email).first()
        if not user:
            return {'message': 'email not found'}, 404
        token = user.generate_recovery_token()
        return {'recovery_code': token}, 200
api.add_resource(GenerateRecoveryCode, '/generate_recovery_code')

class LoginWithRecoveryCode(Resource):
 
    @validate_headers
    def post(self):
        """
        Handles a POST request to log in the user using the recovery code.

        Validates the headers of the request using the `validate_headers` decorator.


        :return: A dictionary with a message and an HTTP status code.
        :rtype: dict
        """
        secret_key = getenv('SECRET_KEY')
        payload = jwt.decode(request.json.get('recovery_code'), secret_key, algorithms=['HS256'])
        user = User.query.filter_by(email=payload.get('email')).first()
        login_user(user)
        return {'message': 'Login successful'}, 200
api.add_resource(LoginWithRecoveryCode, '/login_with_recovery_code')
class CreateGroup(Resource):
    @validate_headers
    @login_required
    def post(self):
        """
        Create a new group.

        Parameters:
            None

        Returns:
            - A dictionary with the message 'Group created' and the status code 201 if the group was successfully created.
            - A dictionary with the message 'Invalid input' and the status code 400 if the input is invalid.
        """
       
        try:
            data = request.get_json()
            name = data.get('name')
            creator = current_user.id
            event_date = data.get('event_date')
            min_gift_price = data.get('min_gift_price')
            max_gift_price = data.get('max_gift_price')
            creator_desired_gift = data.get('creator_desired_gifts')
        except KeyError:
            return {'message': 'Invalid input'}, 400
        

        if name == '' or event_date == '' or min_gift_price == '' or max_gift_price == '':
            return {'message': 'Invalid input'}, 400
        
        if min_gift_price > max_gift_price:
            return {'message': 'Invalid input'}, 400
        
        
    
        group = Group(name, creator, event_date, min_gift_price, max_gift_price)
        db.session.add(group)
        db.session.commit()
        db.session.add(Friend(current_user.id, group.id, creator_desired_gift))
        db.session.commit()

        return {'message': 'Group created'}, 201
api.add_resource(CreateGroup, '/creategroup')

class GetGroups(Resource):
    @validate_headers
    @login_required
    def get(self):
        """
        A function that retrieves a list of groups, this route requires the current user to be a superuser.

        Returns:
            - If the current user is a superuser, a serialized list of all groups.
            - If the current user is not a superuser, a dictionary with a message indicating unauthorized access and a status code of 401.
        """

        if current_user.is_superuser:
            serialized_groups = [group.serialize() for group in Group.query.all()]
            return serialized_groups
        return {'message': 'Unauthorized'}, 401
api.add_resource(GetGroups, '/sugetgroups')

class GetGroupSuperUser(Resource):
    @validate_headers
    @login_required
    def get(self, group_id):
        """
        Retrieves a serialized group object based if the current user is a superuser.

        Parameters:
            group_id (int): The ID of the group to retrieve.

        Returns:
            dict: A serialized group object if the current user is a superuser.
            dict: {'message': 'Unauthorized'} with status code 401 if the current user is not a superuser.
        """
        
        if current_user.is_superuser:
            serialized_group = Group.query.filter_by(id=group_id).first().serialize()
            return serialized_group
        return {'message': 'Unauthorized'}, 401

api.add_resource(GetGroupSuperUser, '/sugetgroup/<string:group_id>')

class GetGroupCreator(Resource):
    @validate_headers
    @login_required
    def get(self):
        """
        Retrieves all groups created by the current user.

        Returns:
            list: A list of serialized group objects representing the groups created by the current user. If no groups are found, an empty list is returned.
        """

        groups = Group.query.filter_by(creator=current_user.id).all()
        serialized_groups = [group.serialize() for group in groups]
        return serialized_groups if serialized_groups else []
api.add_resource(GetGroupCreator, '/getcreatorgroups')

class GetFriendsGroup(Resource):
    @validate_headers
    @login_required
    def get(self, group_id):
        """
        Get the list of friends in a group.

        Parameters:
            group_id (int): The ID of the group.

        Returns:
            list: A list of serialized friend objects.

        Raises:
            dict: A dictionary with an 'message' key and a status code of 401 if the user is not authorized.
        """
        user = current_user
        group = Group.query.filter_by(id=group_id).first()
        friend_user = [friend for friend in group.friends if friend.user_id == user.id]
        if friend_user:
            friends = [friend.serialize() for friend in group.friends]
            return friends
        return {'message': 'Unauthorized'}, 401
api.add_resource(GetFriendsGroup, '/getfriendsgroup/<string:group_id>')

class PerfectDrawnGroup(Resource):
    @validate_headers
    @login_required
    def post(self):
        """
        This function is used to handle the POST request for the API endpoint.
        This endpoint is used to mark a group as "perfect drawn" and draw the secret friends for the group with perfect drawn rules.
        
        Parameters:
            None
        
        Returns:
            A dictionary containing the response message and the corresponding status code.
            If the user is authorized and has admin privileges in the group, the group will be marked as "perfect drawn" and a success message will be returned with a status code of 200.
            If the user is not authorized or does not have admin privileges in the group, an error message will be returned with a status code of 401.
        """
      
        group:Group = Group.query.filter_by(id=request.json.get('group_id')).first()
        friend_user = [friend for friend in group.friends if friend.user_id == current_user.id]
        
        if friend_user:
            if friend_user[0].is_admin:
                group.perfect_drawn()
                return {'message': 'Perfect Drawn'}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(PerfectDrawnGroup, '/perfectdrawngroup')

class ImperfectDrawnGroup(Resource):
    @validate_headers
    @login_required
    def post(self):
        """
        This function handles the POST request for the API endpoint.
        This endpoint is used to mark a group as "imperfect drawn" and draw the secret friends for the group with imperfect drawn rules.
        
        Parameters:
        None
        
        Returns:
        - If the user is authorized and is an admin of the group, it marks the group as imperfectly drawn and returns a success message with status code 200.
        - If the user is not authorized or is not an admin of the group, it returns an unauthorized message with status code 401.
        """
    
       
        group = Group.query.filter_by(id=request.get_json().get('group_id')).first()
        friend_user = [friend for friend in group.friends if friend.user_id == current_user.id]
        if friend_user:
            if friend_user[0].is_admin:
                group.imperfect_drawn()
                return {'message': 'Imperfect Drawn'}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(ImperfectDrawnGroup, '/imperfectdrawngroup')
            

class GetMyFriend(Resource):
    @validate_headers
    @login_required
    def get(self, group_id):
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
        friend_user = [friend for friend in group.friends if friend.user_id == current_user.id]
        if friend_user:
            return{'friend_name': friend_user[0].serialize()['friend_name'], 
                   'friend_id': friend_user[0].friend_id, 
                   'friend_gift':Friend.query.filter_by(user_id=friend_user[0].friend_id).first().gift_desired}, 200
        return {'message': 'Unauthorized'}, 401
api.add_resource(GetMyFriend, '/getmyfriend/<string:group_id>')
