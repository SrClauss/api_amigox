import root_path
root_path.define_sys_path()
import unittest
from app.models import User, Group, Friend
import app.config as app_config
from dotenv import load_dotenv
from config_test import create_db


db, app = app_config.db, app_config.app
load_dotenv()

class TestModels(unittest.TestCase):
    def setUp(self):
       create_db()
    def test_persistence(self):
        with app.app_context():
            self.assertEqual(len(User.query.all()), 4)
            self.assertEqual(len(Group.query.all()), 1)
            self.assertEqual(len(Friend.query.all()), 4)
            group = Group.query.first()
            self.assertEqual(group.description, 'group1')
            self.assertEqual(db.session.query(Friend).where(Friend.group_id == group.id).count(), 4)
    def test_password_check(self):
        with app.app_context():
            user = User.query.filter_by(name='user1').first()
            self.assertTrue(user.check_password('password1'))
            self.assertFalse(user.check_password('password2'))
    
    def test_perfectdraw(self):
        with app.app_context():
            group:Group = Group.query.first()
            group.perfect_drawn()
            self.assertFalse(any(friend.friend_id == friend.user_id for friend in group.friends))
    
    def test_imperfectdraw(self):
        with app.app_context():
            group:Group = Group.query.first()
            group.imperfect_drawn()
            self.assertFalse(any(friend.friend_id == friend.user_id for friend in group.friends))
    def test_kickout(self):
        with app.app_context():
            user = User.query.filter_by(email='email1@example.com').first()
            group = Group.query.first()
            friend = Friend.query.filter_by(group_id = group.id, user_id = user.id).first()
            group.kick_out(friend.user_id)
            self.assertEqual(len(Friend.query.all()), 3)

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()     





if __name__ == '__main__':
    unittest.main()
    
















