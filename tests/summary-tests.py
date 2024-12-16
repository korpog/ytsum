import pytest
from flask import g, session, url_for
from unittest.mock import MagicMock, patch
import sqlite3

from summ.summary import (
    index,
    create,
    get_summary,
    detail,
    update,
    delete,
    add_favorite,
    remove_favorite,
    favorites
)

# Helpers for testing routes that require authentication


def login_user(client, username='test', password='test'):
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    })


@pytest.fixture
def mock_youtube_functions(mocker):
    """Mock YouTube-related functions to prevent actual API calls"""
    mocker.patch('summ.summary.extract_video_id', return_value='test_video_id')
    mocker.patch('summ.summary.get_youtube_title', return_value='Test Video')
    mocker.patch('summ.summary.get_youtube_video_channel_name',
                 return_value='Test Channel')
    mocker.patch('summ.summary.get_transcript', return_value='Test transcript')
    mocker.patch('summ.summary.summarize_text', return_value='Test summary')

# Test index route


def test_index_route(client, app):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Summaries' in response.data


def test_index_route_with_category_filter(client, app):
    with app.app_context():
        db = app.db
        # Ensure a category and summary exist
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        db.commit()

    response = client.get('/?category=Test%20Category')
    assert response.status_code == 200


def test_index_route_with_search_query(client, app):
    response = client.get('/?search=test')
    assert response.status_code == 200

# Test create route


def test_create_route_get(client, app):
    # Login first
    login_user(client)

    response = client.get('/create')
    assert response.status_code == 200
    assert b'Create Summary' in response.data


def test_create_route_post_success(client, app, mock_youtube_functions):
    # Login first
    login_user(client)

    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        db.execute('SELECT id FROM category WHERE category_name = ?',
                   ('Test Category',)).fetchone()
        db.commit()

    # Get the category ID
    with app.app_context():
        category_id = app.db.execute(
            'SELECT id FROM category').fetchone()['id']

    # Post data to create route
    response = client.post('/create', data={
        'yt_url': 'https://youtube.com/watch?v=test',
        'category_name': category_id
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check if redirected to index
    assert b'Summaries' in response.data


def test_create_route_missing_url(client, app):
    # Login first
    login_user(client)

    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        db.commit()

    # Get the category ID
    with app.app_context():
        category_id = app.db.execute(
            'SELECT id FROM category').fetchone()['id']

    # Post data without URL
    response = client.post('/create', data={
        'category_name': category_id
    })

    assert b'Youtube URL is required' in response.data

# Test detail route


def test_detail_route(client, app):
    # First, create a summary
    with app.app_context():
        # Ensure a category and user exist
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        db.execute('SELECT id FROM category')
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Access the detail page
    response = client.get(f'/detail/{summary_id}')
    assert response.status_code == 200
    assert b'Test Title' in response.data

# Test update route


def test_update_route_get(client, app):
    # Login first
    login_user(client)

    # First, create a summary
    with app.app_context():
        # Ensure a category and user exist
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Access the update page
    response = client.get(f'/update/{summary_id}')
    assert response.status_code == 200
    assert b'Test Title' in response.data


def test_update_route_post(client, app):
    # Login first
    login_user(client)

    # First, create a summary
    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Update the summary
    response = client.post(f'/update/{summary_id}', data={
        'yt_title': 'Updated Title',
        'summary_text': 'Updated Summary',
        'category_name': category_id,
        'yt_channel_name': 'Updated Channel'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check if redirected to index
    assert b'Summaries' in response.data

# Test delete route


def test_delete_route(client, app):
    # Login first
    login_user(client)

    # First, create a summary
    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Delete the summary
    response = client.post(f'/delete/{summary_id}', follow_redirects=True)

    assert response.status_code == 200
    # Check if redirected to index
    assert b'Summaries' in response.data

# Test favorite routes


def test_add_favorite(client, app):
    # Login first
    login_user(client)

    # First, create a summary
    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Add to favorites
    response = client.post(f'/favorite/{summary_id}', follow_redirects=True)

    assert response.status_code == 200
    assert b'Summary added to favorites' in response.data


def test_remove_favorite(client, app):
    # Login first
    login_user(client)

    # First, create a summary and add to favorites
    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

        # Add to favorites first
        db.execute('''
            INSERT INTO user_favorite_summary (user_id, summary_id) 
            VALUES (?, ?)
        ''', (1, summary_id))
        db.commit()

    # Remove from favorites
    response = client.post(f'/unfavorite/{summary_id}', follow_redirects=True)

    assert response.status_code == 200
    assert b'Summary removed from favorites' in response.data

# Test favorites route


def test_favorites_route(client, app):
    # Login first
    login_user(client)

    # First, create a summary and add to favorites
    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute('INSERT INTO category (category_name) VALUES (?)',
                   ('Test Category',))
        category_id = db.execute('SELECT id FROM category').fetchone()['id']

        # Insert a summary
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'test_url', 'Test Title', 'Test Channel', 1, category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

        # Add to favorites
        db.execute('''
            INSERT INTO user_favorite_summary (user_id, summary_id) 
            VALUES (?, ?)
        ''', (1, summary_id))
        db.commit()

    # Access favorites route
    response = client.get('/favorites')

    assert response.status_code == 200
    assert b'Test Title' in response.data


#########


# Helpers for testing routes that require authentication

def login_user(client, username='test', password='test'):
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    })


@pytest.fixture
def mock_youtube_functions(mocker):
    """Mock YouTube-related functions to prevent actual API calls"""
    mocker.patch('summ.summary.extract_video_id', return_value='test_video_id')
    mocker.patch('summ.summary.get_youtube_title',
                 return_value='Unique Test Video Title')
    mocker.patch('summ.summary.get_youtube_video_channel_name',
                 return_value='Test Channel')
    mocker.patch('summ.summary.get_transcript', return_value='Test transcript')
    mocker.patch('summ.summary.summarize_text', return_value='Test summary')

# Test index route


def test_index_route(client, app):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Summaries' in response.data


def test_index_route_with_category_filter(client, app):
    with app.app_context():
        db = app.db
        # Ensure a category and summary exist
        db.execute(
            'INSERT OR IGNORE INTO category (category_name) VALUES (?)', ('Test Category',))
        db.commit()

    response = client.get('/?category=Test%20Category')
    assert response.status_code == 200


def test_index_route_with_search_query(client, app):
    response = client.get('/?search=test')
    assert response.status_code == 200

# Test create route


def test_create_route_get(client, app):
    # Login first
    login_user(client)

    response = client.get('/create')
    assert response.status_code == 200
    assert b'Create Summary' in response.data


def test_create_route_post_success(client, app, mock_youtube_functions):
    # Login first
    login_user(client)

    with app.app_context():
        # Ensure a category exists
        db = app.db
        # Ensure user exists
        db.execute(
            'INSERT OR IGNORE INTO user (username, password) VALUES (?, ?)', ('test', 'test'))
        db.execute(
            'INSERT OR IGNORE INTO category (category_name) VALUES (?)', ('Test Category',))
        db.commit()

    # Get the category ID
    with app.app_context():
        category_id = app.db.execute(
            'SELECT id FROM category WHERE category_name = ?', ('Test Category',)).fetchone()['id']

    # Post data to create route
    response = client.post('/create', data={
        'yt_url': 'https://youtube.com/watch?v=unique_test_video',
        'category_name': category_id
    }, follow_redirects=True)

    assert response.status_code == 200
    # Check if redirected to index
    assert b'Summaries' in response.data


def test_create_route_missing_url(client, app):
    # Login first
    login_user(client)

    with app.app_context():
        # Ensure a category exists
        db = app.db
        db.execute(
            'INSERT OR IGNORE INTO category (category_name) VALUES (?)', ('Test Category',))
        db.commit()

    # Get the category ID
    with app.app_context():
        category_id = app.db.execute(
            'SELECT id FROM category').fetchone()['id']

    # Post data without URL
    response = client.post('/create', data={
        'category_name': category_id
    })

    assert b'Youtube URL is required' in response.data

# Similar modifications for other test functions...
# (Continuing with the same pattern of ensuring unique constraints and proper user/category insertions)

# Example of modified test_detail_route


def test_detail_route(client, app):
    # First, create a summary
    with app.app_context():
        # Ensure a category and user exist
        db = app.db
        db.execute(
            'INSERT OR IGNORE INTO user (username, password) VALUES (?, ?)', ('test', 'test'))
        db.execute(
            'INSERT OR IGNORE INTO category (category_name) VALUES (?)', ('Test Category',))
        db.commit()

        category_id = db.execute(
            'SELECT id FROM category WHERE category_name = ?', ('Test Category',)).fetchone()['id']

        # Insert a summary with unique constraints
        db.execute('''
            INSERT INTO summary 
            (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test Summary', 'Test Transcript', 'https://unique.youtube.com/video1',
              'Unique Video Title 1', 'Test Channel',
              db.execute('SELECT id FROM user WHERE username = ?',
                         ('test',)).fetchone()['id'],
              category_id))
        db.commit()

        # Get the summary ID
        summary_id = db.execute('SELECT id FROM summary').fetchone()['id']

    # Access the detail page
    response = client.get(f'/detail/{summary_id}')
    assert response.status_code == 200
    assert b'Unique Video Title 1' in response.data

# Repeat similar modifications for other test functions
# Ensure unique URLs, titles, and proper user/category insertions
