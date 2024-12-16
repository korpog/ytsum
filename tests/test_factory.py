from summ import create_app
from flask.testing import FlaskClient


def test_config() -> None:
    """Test the configuration of the Flask app."""
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing
