from app.models import User, Group, Friend, db, app
import datetime

def create_db():
    """
    Creates a new database and populates it with initial data.
    
    This function creates a new database by dropping all existing tables and then creating new ones using the models defined in the codebase. It then populates the database with initial data, including creating a set of users, a group, and some friends associated with the group.
    
    Parameters:
        None
    
    Returns:
        app (Flask): The Flask app object with the testing flag set to True.
    """
    with app.app_context():
        
        db.session.close()
        db.drop_all()
        db.create_all()

        users = [
            User('user1', 'email1@example.com', 'password1'),
            User('user2', 'email2@example.com', 'password2'),
            User('user3', 'email3@example.com', 'password3'),
            User('user4', 'email4@example.com', 'password4')
        ]
        users[0].is_superuser = True
        
        db.session.add_all(users)

        db.session.commit()

        group1 = Group('group1', users[0].id, datetime.datetime.now(), 100, 200)
        db.session.add(group1)

        db.session.commit()

        friends = [
            Friend(users[0].id, group1.id, 'gift1'),
            Friend(users[1].id, group1.id, 'gift2'),
            Friend(users[2].id, group1.id, 'gift3'),
            Friend(users[3].id, group1.id, 'gift4')
        ]
        friends[0].is_admin = True
        db.session.add_all(friends)

        db.session.commit()

        app.testing = True
        return app
