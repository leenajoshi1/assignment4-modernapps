"""Integration tests against a temporary database and upload directory."""
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
import sys

_temp = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(_temp.name) / 'test.db')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from application import app, db, Admin, GeneralUser, Photos
from PIL import Image


def image_bytes():
    output = BytesIO()
    Image.new('RGB', (40, 30), '#bf5700').save(output, format='PNG')
    return BytesIO(output.getvalue())


class PortalTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, UPLOAD_FOLDER=str(Path(_temp.name) / self._testMethodName))
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.assertEqual(self.client.post('/api/admin', json={'username': 'admin', 'password': 'test-password'}).status_code, 201)

    def login(self):
        return self.client.post('/api/adminlogin', json={'username': 'admin', 'password': 'test-password'})

    def upload(self, name='campus.png', taken='2026-11-10', tags='Austin, campus', comments='A sunny afternoon.'):
        return self.client.post('/api/upload', data=dict(photo_file=(image_bytes(), name), date_taken=taken, tags=tags, comments=comments))

    def test_admin_singleton_and_password(self):
        self.assertEqual(self.client.post('/api/admin', json={'username':'other','password':'other'}).status_code, 409)
        self.assertEqual(self.client.post('/api/adminlogin', json={'username':'admin','password':'wrong'}).status_code, 401)
        self.assertEqual(self.login().status_code, 200)
        admins = self.client.get('/api/admin').json['admins']
        self.assertEqual(admins, [{'id':1,'username':'admin'}])
        with app.app_context():
            self.assertNotEqual(Admin.query.first().password, 'test-password')

    def test_general_users_and_authorization(self):
        self.assertEqual(self.client.get('/api/photos').status_code, 401)
        self.assertEqual(self.client.get('/static/images/photos/campus.png').status_code, 401)
        self.assertEqual(self.client.post('/api/generaluser', json={'gmail':'viewer@gmail.com'}).status_code, 401)
        self.login()
        self.upload()
        self.assertEqual(self.client.post('/api/generaluser', json={'gmail':'bad@example.com'}).status_code, 400)
        self.assertEqual(self.client.post('/api/generaluser', json={'gmail':'Viewer@gmail.com'}).status_code, 201)
        self.assertEqual(self.client.post('/api/generaluser', json={'gmail':'viewer@gmail.com'}).status_code, 409)
        self.assertEqual(len(self.client.get('/api/generaluser').json['generalusers']), 1)
        self.assertEqual(self.client.post('/api/logout').json['usertype'], 'admin')
        self.assertEqual(self.client.post('/api/generaluserlogin', json={'gmail':'missing@gmail.com'}).status_code, 401)
        self.assertEqual(self.client.post('/api/generaluserlogin', json={'gmail':'VIEWER@gmail.com'}).status_code, 200)
        self.assertEqual(len(self.client.get('/api/photos').json['photos']), 1)
        with self.client.get('/static/images/photos/campus.png') as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.upload('forbidden.png').status_code, 403)
        self.assertEqual(self.client.get('/api/admin').status_code, 403)
        self.assertEqual(self.client.post('/api/logout').json['usertype'], 'generaluser')
        self.assertEqual(self.client.get('/api/session').status_code, 401)

    def test_upload_persistence_and_comments(self):
        self.login()
        result = self.upload(comments='First line\nSecond line <script>literal</script>')
        self.assertEqual(result.status_code, 201)
        self.assertEqual(self.upload().status_code, 409)
        with app.app_context():
            db.session.remove()
            self.assertEqual(Photos.query.first().tags, 'Austin, campus')
        self.assertEqual(self.client.get('/api/photos').json['photos'][0]['date_taken'], '2026-11-10')
        self.assertEqual(self.client.get('/api/photos/campus.png/comments').json['comments'], 'First line\nSecond line <script>literal</script>')
        self.assertEqual(self.client.get('/api/photos/missing.png/comments').status_code, 404)
        with self.client.get('/static/images/photos/campus.png') as response:
            self.assertEqual(response.status_code, 200)

    def test_search_all_modes_and_empty_results(self):
        self.login()
        self.upload()
        self.upload('lake.png', '2026-10-01', 'nature, water')
        for kind, query, expected in [('Name','CAMP',1),('Tags','aUsTiN',1),('Date','2026-10-01',1),('Name','missing',0),('Name','%',0),('Tags','',2)]:
            response = self.client.post('/api/search', json={'type':kind,'query':query})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json['results']), expected)
        self.assertEqual(self.client.post('/api/search', json={'type':'Date','query':'bad'}).status_code, 400)
        self.assertEqual(self.client.post('/api/search', json={'type':'bad','query':''}).status_code, 400)

    def test_invalid_uploads(self):
        self.login()
        self.assertEqual(self.client.post('/api/upload', data={}).status_code, 400)
        self.assertEqual(self.upload(taken='not-a-date').status_code, 400)
        self.assertEqual(self.client.post('/api/upload', data=dict(photo_file=(BytesIO(b'fake image'), 'fake.png'),date_taken='2026-11-10')).status_code, 400)
        self.assertEqual(self.upload(name='bad.txt').status_code, 400)

if __name__ == '__main__':
    unittest.main()
