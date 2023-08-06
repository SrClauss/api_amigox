from app.models import User, Group, Friend
import app.config as app_config
import datetime
from app.rest import api


app, db = app_config.app, app_config.db

if __name__ == '__main__':
   
    with app.app_context():
            
        db.drop_all()
        db.create_all()

        
        users = [
            User('user1', 'email1@example.com','www.instagram.com/user1', 'password1'),
            User('user2', 'email2@example.com','www.instagram.com/user2', 'password2'),
            User('user3', 'email3@example.com','www.instagram.com/user3', 'password3'),
            User('user4', 'email4@example.com','www.instagram.com/user4', 'password4')
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
    
    import logging
    logging.basicConfig(filemode='api.log', level=logging.DEBUG)
    app.run()