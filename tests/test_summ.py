import pytest
from flask import Flask
from flask.testing import FlaskClient
from summ.db import get_db
from typing import Any


def test_index(client: FlaskClient, auth: object) -> None:
    response = client.get('/')
    assert b"Log In" in response.data
    assert b"Register" in response.data
    assert b'YouTube Title' in response.data
    assert b'Channel' in response.data
    assert b'Category' in response.data
    assert b'Date' in response.data
    assert b'Created by' in response.data
    assert b'https://www.youtube.com/watch?v=dQw4w9WgXcQ"' in response.data

    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'Favorite' in response.data


def test_index_route_with_category_filter(client: FlaskClient):
    response = client.get('/?category=Music')
    assert response.status_code == 200


def test_index_route_with_search_query(client: FlaskClient):
    response = client.get('/?search=title')
    assert response.status_code == 200


def test_detail(client: FlaskClient):
    response = client.get('/detail/1')
    assert response.status_code == 200
    assert b'Summary Details' in response.data


def test_detail_nonexisting_summary(client: FlaskClient):
    response = client.get('/detail/1000')
    assert response.status_code == 404


@pytest.mark.parametrize('path', ['/create', '/update/1', '/delete/1'])
def test_login_required(client: FlaskClient, path: str) -> None:
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app: Flask, client: FlaskClient, auth: object) -> None:
    with app.app_context():
        db = get_db()
        db.execute('UPDATE summary SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    assert client.post('/update/1').status_code == 403
    assert client.post('/delete/1').status_code == 403
    assert b'href="/update/1"' not in client.get('/').data


@pytest.mark.parametrize('path', ['/update/5', '/delete/5'])
def test_exists_required(client: FlaskClient, auth: object, path: str) -> None:
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={
        'yt_url': 'https://www.youtube.com/watch?v=MGXSPf9b-xI',
        'category_name': 2})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM summary').fetchone()[0]
        assert count == 3


def test_create_duplicate(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()

    client.post('/create', data={
        'yt_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'category_name': 2})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM summary').fetchone()[0]
        assert count == 2


def test_create_no_url(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    response = client.post('/create', data={'yt_url': '',
                                            'category_name': 2}, follow_redirects=True)

    assert b'Youtube URL is required' in response.data
    assert response.status_code == 200


def test_create_summary_no_category(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    response = client.post('/create', data={
        'yt_url': 'https://youtube.com/watch?v=test',
        'category_name': ''
    }, follow_redirects=True)

    assert b'Category is required' in response.data
    assert response.status_code == 200


def test_create_summary_duplicate_title(client: FlaskClient, auth: object, app: Flask, mocker: Any) -> None:
    auth.login()
    mocker.patch('summ.llm.extract_video_id', return_value='test_vid')
    mocker.patch('summ.llm.get_youtube_title',
                 return_value='Test Video Title')
    mocker.patch('summ.llm.get_youtube_video_channel_name',
                 return_value='Test Channel')
    mocker.patch('summ.llm.get_transcript', return_value='Test transcript')
    mocker.patch('summ.llm.summarize_text', return_value='Test summary')

    with app.app_context():
        db = get_db()
        client.post('/create', data={
            'yt_url': 'https://youtube.com/watch?v=test1',
            'category_name': 1
        }, follow_redirects=True)

        db.execute(
            'INSERT INTO summary (yt_title, yt_url, summary_text, transcript, yt_channel_name, author_id, category_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            ('Test Video Title', 'https://youtube.com/watch?v=existing', 'Existing summary',
                'Existing transcript', 'Test Channel', 1, 1)
        )
        db.commit()

        response2 = client.post('/create', data={
            'yt_url': 'https://youtube.com/watch?v=test2',
            'category_name': 1
        }, follow_redirects=True)

        assert response2.status_code == 200


def test_update(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    client.post('/update/1', data={
        'yt_title': 'new fake title3',
        'yt_channel_name': 'WTF2',
        'summary_text': 'new fake summary3',
        'category_name': 2
    })

    with app.app_context():
        db = get_db()
        summary = db.execute('SELECT * FROM summary WHERE id = 1').fetchone()
        assert summary['yt_title'] == 'new fake title3'


@pytest.mark.parametrize('path', ['/create', '/update/1'])
def test_create_update_validate(client: FlaskClient, auth: object, path: str) -> None:
    auth.login()
    response = client.post(path, data={
        'yt_title': '',
        'yt_channel_name': 'WTF2',
        'summary_text': 'new fake summary3',
        'category_name': 2})
    assert response.status_code == 400


def test_delete(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    response = client.post('/delete/1')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM summary WHERE id = 1').fetchone()
        assert post is None


def test_add_favorite(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()
    response = client.post('/favorite/1', follow_redirects=True)
    with app.app_context():
        db = get_db()
        count = db.execute(
            'SELECT COUNT(*) FROM user_favorite_summary WHERE user_id = 1 AND summary_id = 1').fetchone()[0]
        assert count == 1

    assert response.status_code == 200


def test_add_favorite_nonexistent_summary(client: FlaskClient, auth: object) -> None:
    auth.login()
    response = client.post('/favorite/9999')
    assert response.status_code == 404


def test_add_favorite_duplicate(client: FlaskClient, auth: object, app: Flask) -> None:
    auth.login()

    response1 = client.post('/favorite/1', follow_redirects=True)
    assert response1.status_code == 200

    response2 = client.post('/favorite/1', follow_redirects=True)
    assert response2.status_code == 200

    with app.app_context():
        db = get_db()
        count = db.execute(
            'SELECT COUNT(*) FROM user_favorite_summary WHERE user_id = 1 AND summary_id = 1'
        ).fetchone()[0]
        assert count == 1


def test_add_favorite_unauthenticated(client: FlaskClient) -> None:
    response = client.post('/favorite/1')

    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_remove_favorite(client: FlaskClient, auth: object, app: Flask):
    auth.login()
    response = client.post('/unfavorite/1', follow_redirects=True)

    with app.app_context():
        db = get_db()
        count = db.execute(
            'SELECT COUNT(*) FROM user_favorite_summary WHERE user_id = 1 AND summary_id = 1'
        ).fetchone()[0]
        assert count == 0

    assert response.status_code == 200


def test_favorites_authenticated(client: FlaskClient, auth: object):
    auth.login()
    response = client.get("/favorites")

    assert response.status_code == 200


def test_favorites_unauthorized(client):
    response = client.get("/favorites")

    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
