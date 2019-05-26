'''
单元测试
'''

from datetime import datetime, timedelta
from unittest import mock
import json

from requests.models import Response
import jwt
import pytest

from instance.config import JWT_KEY
from novel.models import User, Book, BookExtra
from novel import create_app

app = create_app()
app.app_context().push()

NOW = datetime.utcnow()
PAYLOAD = {
    'iss': 'rrcgat',
    'exp': NOW + timedelta(hours=3),
    'iat': NOW
}
TOKEN = jwt.encode(PAYLOAD, JWT_KEY,
                   algorithm='HS256')

HEADERS = {
    'Authorization': str(TOKEN, 'utf-8'),
    'Sid': 'session_id'
}

BOOK = Book.query.get(1)
PUB_INFO = BookExtra.query.get(1).info


class MockRespone(Response):
    '''Mock requests response'''

    def __init__(self, content=None, status_code=200):
        super(MockRespone, self).__init__()
        self._content = content
        self.status_code = status_code


def test_login_without_wechat_code(client):
    '''验证登录时没有 code'''

    assert client.get('/api/login').status_code == 400


@mock.patch('requests.get')
def test_login(mock_get, client):
    global HEADERS
    mock_get.return_value = MockRespone(b'{"openid":"openid"}')

    assert client.get('/api/login?code=code',
                      headers=HEADERS).status_code == 200

    HEADERS['Sid'] = User.query.filter_by(open_id='openid').first().session_id


def test_wechat_api_without_authority(client):
    '''未经过验证'''

    assert client.get('/api/s').status_code == 401
    assert client.get('/api/stars').status_code == 401
    assert client.post('/api/stars').status_code == 401
    assert client.delete('/api/stars').status_code == 401
    assert client.get('/api/books').status_code == 401
    assert client.get('/api/authors').status_code == 401


def test_search(client):
    assert client.get('/api/s?kw={}'.format(BOOK.book_name),
                      headers=HEADERS).status_code == 200

    assert client.get('/api/s?kw=Book-not-exists',
                      headers=HEADERS).status_code == 404


@pytest.mark.incremental
class TestStar():
    '''收藏接口测试'''

    def test_get(self, client):
        assert client.get('/api/stars', headers=HEADERS).status_code == 200
        assert client.get('/api/stars?type=like',
                          headers=HEADERS).status_code == 200
        assert client.get('/api/stars?type=dislike',
                          headers=HEADERS).status_code == 200

    def test_post(self, client):
        rv = client.post('/api/stars',
                         data=json.dumps({'book_id': 1, 'star': 1}),
                         content_type='application/json',
                         headers=HEADERS)
        assert rv.status_code == 201
        rv = client.post('/api/stars',
                         data=json.dumps({'book_id': -1, 'star': 1}),
                         content_type='application/json',
                         headers=HEADERS)
        assert rv.status_code == 404

    def test_delete(self, client):
        rv = client.delete('/api/stars',
                           data=json.dumps({'book_id': 1}),
                           content_type='application/json',
                           headers=HEADERS)
        assert rv.status_code == 204
        rv = client.delete('/api/stars',
                           data=json.dumps({'book_id': -1}),
                           content_type='application/json',
                           headers=HEADERS)
        assert rv.status_code == 404


class TestBook():
    def test_get(self, client):
        assert client.get('/api/books?id=-1',
                          headers=HEADERS).status_code == 404
        assert client.get('/api/books?id=1',
                          headers=HEADERS).status_code == 200
        with mock.patch('novel.spider.QiDian') as mc:
            instance = mc.return_value
            instance.book_info.return_value = {}
            rv = client.get('/api/books?name=Book-not-exitst',
                            headers=HEADERS)
            assert rv.status_code == 404
            instance.book_info.return_value = BOOK.json(True)
            instance.pub_info = PUB_INFO
            rv = client.get('/api/books?name={}'.format(BOOK.book_name),
                            headers=HEADERS)
            assert rv.status_code == 200

    def test_post(self, client):
        # 参数缺失
        assert client.post('/api/books',
                           data=json.dumps({'id': 1}),
                           content_type='application/json',
                           headers=HEADERS).status_code == 400
        # 标签参数无效
        assert client.post('/api/books',
                           data=json.dumps({'tag': '*.,(!', 'id': 1}),
                           content_type='application/json',
                           headers=HEADERS).status_code == 400

        # TODO 敏感词
        # assert client.post('/api/books',
        #                    data=json.dumps({'tag': 'tmd', 'id': 1}),
        #                    content_type='application/json',
        #                    headers=HEADERS).status_code == 403

        assert client.post('/api/books',
                           data=json.dumps({'id': 1, 'tag': 'new_tag'}),
                           content_type='application/json',
                           headers=HEADERS).status_code == 201
        # 添加相同 tag，测试幂等
        assert client.post('/api/books',
                           data=json.dumps({'id': 1, 'tag': 'new_tag'}),
                           content_type='application/json',
                           headers=HEADERS).status_code == 201

    def put(self, client):
        assert client.put('/api/books',
                          data=json.dumps({}),
                          content_type='application/json',
                          headers=HEADERS).status_code == 400
        assert client.put('/api/books',
                          data=json.dumps({'book_id': BOOK.id,
                                           'status': BOOK.status}),
                          content_type='application/json',
                          headers=HEADERS).status_code == 200

    def delete(self, client):
        assert client.delete('/api/books',
                             data=json.dumps({'book_id': 1, 'tag': 'new_tag'}),
                             content_type='application/json',
                             headers=HEADERS).status_code == 204
        # 测试幂等
        assert client.delete('/api/books',
                             data=json.dumps({'book_id': 1, 'tag': 'new_tag'}),
                             content_type='application/json',
                             headers=HEADERS).status_code == 204


class TestAuthor():
    def test_get(self, client):
        # TODO 添加测试
        pass
