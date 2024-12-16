import sqlite3
from typing import List, Union
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort

from summ.auth import login_required
from summ.db import get_db
from summ.llm import get_transcript, extract_video_id, summarize_text, get_youtube_title, get_youtube_video_channel_name

bp = Blueprint('summary', __name__)


@bp.route('/')
def index() -> str:
    db = get_db()

    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')

    query = '''
    SELECT s.id, s.yt_url, s.yt_title, s.yt_channel_name, 
           s.transcript, s.summary_text, s.author_id, 
           s.created_at, u.username, c.category_name
    FROM summary s 
    INNER JOIN user u ON s.author_id = u.id
    INNER JOIN category c ON c.id = s.category_id
    WHERE 1=1
    '''

    params = []

    if category_filter:
        query += ' AND c.category_name = ?'
        params.append(category_filter)

    if search_query:
        query += ' AND s.yt_title LIKE ?'
        params.append(search_query)

    query += ' ORDER BY s.created_at DESC'

    summaries = db.execute(query, params).fetchall()

    categories = db.execute(
        'SELECT id, category_name FROM category').fetchall()

    user_favorites: List[int] = []

    if g.user:
        user_favorites = [f['summary_id'] for f in db.execute(
            'SELECT summary_id FROM user_favorite_summary WHERE user_id = ?',
            (g.user['id'],)
        ).fetchall()]

    return render_template(
        'summary/index.html',
        summaries=summaries,
        categories=categories,
        selected_category=category_filter,
        search_query=search_query,
        user_favorites=user_favorites
    )


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create() -> Union[str, Response]:
    db = get_db()
    categories = db.execute(
        'SELECT id, category_name FROM category').fetchall()

    if request.method == 'POST':
        yt_url = request.form['yt_url']
        category_id = request.form['category_name']
        error = None

        if not yt_url:
            error = 'Youtube URL is required'

        if not category_id:
            error = 'Category is required'

        if error is not None:
            flash(error)
        else:
            try:
                vid_id = extract_video_id(yt_url)
                yt_title = get_youtube_title(yt_url)
                yt_channel_name = get_youtube_video_channel_name(yt_url)
                transcript = get_transcript(vid_id)
                summary_text = summarize_text(text=transcript)

                db.execute(
                    'INSERT INTO summary (summary_text, transcript, yt_url, yt_title, yt_channel_name, author_id, category_id)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (summary_text, transcript, yt_url, yt_title, yt_channel_name, g.user['id'], category_id))
                db.commit()
                return redirect(url_for('summary.index'))

            except sqlite3.IntegrityError:
                existing_summary = db.execute(
                    'SELECT * FROM summary WHERE yt_title = ?',
                    (yt_title,)
                ).fetchone()

                if existing_summary:
                    flash(f'A summary for "{yt_title}" already exists.')
                    return render_template('summary/create.html', categories=categories)

    return render_template('summary/create.html', categories=categories)


def get_summary(id: int, check_author: bool = True) -> dict:
    summary = get_db().execute(
        'SELECT s.id, s.yt_url, s.yt_title, s.yt_channel_name, s.transcript, s.summary_text, s.author_id, s.created_at, u.username, c.category_name'
        ' FROM summary s INNER JOIN user u ON s.author_id = u.id'
        ' INNER JOIN category c ON c.id = s.category_id'
        ' WHERE s.id = ?',
        (id,)
    ).fetchone()

    if summary is None:
        abort(404, f"Summary id {id} doesn't exist.")

    if check_author and summary['author_id'] != g.user['id']:
        abort(403)

    return summary


@bp.route('/detail/<int:id>', methods=('GET',))
def detail(id: int) -> str:
    summary = get_summary(id, check_author=False)
    return render_template('summary/detail.html', summary=summary)


@bp.route('/update/<int:id>', methods=('GET', 'POST'))
@login_required
def update(id: int) -> Union[str, Response]:
    summary = get_summary(id)
    categories = get_db().execute(
        'SELECT id, category_name FROM category').fetchall()

    if request.method == 'POST':
        yt_title = request.form['yt_title']
        summary_text = request.form['summary_text']
        category_id = request.form['category_name']
        yt_channel_name = request.form['yt_channel_name']
        error = None

        if not yt_title:
            error = 'YouTube title is required.'

        if error is not None:
            flash('YouTube title is required.')
            return render_template('summary/update.html', summary=summary), 400
        else:
            db = get_db()
            db.execute(
                'UPDATE summary SET yt_title = ?, yt_channel_name = ?, summary_text = ?, category_id = ?'
                ' WHERE id = ?',
                (yt_title, yt_channel_name, summary_text, category_id, id)
            )
            db.commit()
            return redirect(url_for('summary.index'))

    return render_template('summary/update.html', summary=summary, categories=categories)


@bp.route('/delete/<int:id>', methods=('POST',))
@login_required
def delete(id: int) -> Response:
    get_summary(id)
    db = get_db()
    db.execute('DELETE FROM summary WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('summary.index'))


@bp.route('/favorite/<int:id>', methods=('POST',))
@login_required
def add_favorite(id: int) -> Response:
    db = get_db()

    summary = get_summary(id, check_author=True)

    if summary is None:
        abort(404, f"Summary id {id} doesn't exist.")

    try:
        db.execute(
            'INSERT INTO user_favorite_summary (user_id, summary_id) VALUES (?, ?)',
            (g.user['id'], id)
        )
        db.commit()
        flash('Summary added to favorites')
    except sqlite3.IntegrityError:
        flash('Summary is already in your favorites')

    return redirect(url_for('summary.index'))


@bp.route('/unfavorite/<int:id>', methods=('POST',))
@login_required
def remove_favorite(id: int) -> Response:
    db = get_db()

    db.execute(
        'DELETE FROM user_favorite_summary WHERE user_id = ? AND summary_id = ?',
        (g.user['id'], id)
    )
    db.commit()
    flash('Summary removed from favorites.')

    return redirect(url_for('summary.favorites'))


@bp.route('/favorites')
@login_required
def favorites() -> str:
    db = get_db()

    query = '''
    SELECT s.id, s.yt_url, s.yt_title, s.yt_channel_name, 
           s.transcript, s.summary_text, s.author_id, 
           s.created_at, u.username, c.category_name
    FROM summary s 
    INNER JOIN user_favorite_summary uf ON s.id = uf.summary_id
    INNER JOIN user u ON s.author_id = u.id
    INNER JOIN category c ON c.id = s.category_id
    WHERE uf.user_id = ?
    ORDER BY s.created_at DESC
    '''

    favorites = db.execute(query, (g.user['id'],)).fetchall()

    return render_template(
        'summary/favorites.html',
        summaries=favorites
    )
