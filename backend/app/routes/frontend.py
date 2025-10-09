# backend/app/routes/frontend.py

import os

from app.config.constants import FRONTEND_DIST_DIR
from flask import Blueprint, current_app, send_from_directory

# Create a blueprint named 'frontend'
frontend = Blueprint("frontend", __name__)


@frontend.route("/", defaults={"path": ""})
@frontend.route("/<path:path>")
def catch_all(path):
    """
    Serve the frontend single-page app for all non-API routes.
    """

    # If request targets backend static assets, serve from Flask static folder directly
    if path.startswith("static/"):
        # Strip the "static/" prefix and serve from the app's static folder
        static_rel = path[len("static/") :]
        return send_from_directory(current_app.static_folder, static_rel)

    # Path to the built frontend directory (adjust if your structure changes)
    frontend_dist_dir = FRONTEND_DIST_DIR

    # Serve built frontend assets (e.g., /assets/*.js, /assets/*.css)
    requested_file = os.path.join(frontend_dist_dir, path)
    if path and os.path.exists(requested_file):
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
