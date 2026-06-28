"""Production WSGI entry point for pyNance.

Used by gunicorn in the Docker deployment. This module-level ``app``
lets gunicorn import the Flask application directly.
"""

from app import create_app

app = create_app()
