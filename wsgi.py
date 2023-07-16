from app.models import db, User, Group, Friend, app
import datetime

from app.rest import api


if __name__ == '__main__':
   
    with app.app_context():
            
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
    
    app.run()