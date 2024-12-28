import os
from typing import Optional, Dict, Any, Union

from flask import Flask
from transformers import pipeline, Pipeline

from . import db, auth, llm, summary


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        test_config (Optional[Dict[str, Any]], optional): Configuration for testing. 
                                                          Defaults to None.

    Returns:
        Flask: Configured Flask application
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'summ.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.model_pipeline: Union[Pipeline,
                              None] = llm.get_summarizer()  # type: ignore

    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(summary.bp)
    app.add_url_rule('/', endpoint='index')

    return app
