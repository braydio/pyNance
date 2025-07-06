# backend/app/routes/frontend.py

import os

from app.config.constants import FRONTEND_DIST_DIR
from flask import Blueprint, send_from_directory

# Create a blueprint named 'frontend'
frontend = Blueprint("frontend", __name__)


@frontend.route("/", defaults={"path": ""})
@frontend.route("/<path:path>")
def catch_all(path):
    """
    Serve the frontend single-page app for all non-API routes.
    """

    # Path to the built frontend directory (adjust if your structure changes)
    frontend_dist_dir = os.path.join(FRONTEND_DIST_DIR, path)

    # Serve static assets (e.g., /assets/*.js, /assets/*.css)
    requested_file = os.path.join(frontend_dist_dir, path)
    if path != "" and os.path.exists(requested_file):
        return send_from_directory(frontend_dist_dir, path)

    # If not an asset, serve index.html for SPA routing
    index_path = os.path.join(frontend_dist_dir, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(frontend_dist_dir, "index.html")

    # If frontend is not built yet
    return (
        "Frontend not built yet. Please run `npm run build` inside the frontend directory.",
        404,
    )
