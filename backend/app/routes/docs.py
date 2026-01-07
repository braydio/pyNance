"""Expose lightweight API documentation in HTML and JSON forms."""

from flask import Blueprint, current_app, jsonify, render_template_string

docs = Blueprint("docs", __name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <style>
        body { font-family: monospace; background: #111; color: #eee; padding: 20px; }
        h1 { color: #74c0fc; }
        .group { margin-top: 20px; }
        .group-name { color: #4dabf7; font-size: 20px; margin-bottom: 5px; }
        .route { margin-left: 20px; margin-bottom: 4px; }
        .method { padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        .GET { background: #2f9e44; }
        .POST { background: #1971c2; }
        .PUT { background: #d9480f; }
        .DELETE { background: #c92a2a; }
        .PATCH { background: #6741d9; }
    </style>
</head>
<body>
    <h1>pyNance API Documentation</h1>
    <p>Auto-generated from Flask url_map</p>

    {% for group, routes in grouped.items() %}
        <div class="group">
            <div class="group-name">{{ group }}</div>
            {% for r in routes %}
                <div class="route">
                    <span>{{ r.rule }}</span>
                    {% for m in r.methods %}
                        <span class="method {{ m }}">{{ m }}</span>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
    {% endfor %}
</body>
</html>
"""


def _collect_routes():
    """Return grouped route metadata from Flask url_map."""
    rules = current_app.url_map.iter_rules()

    routes = []
    for rule in rules:
        # Ignore static files and OPTIONS/HEAD auto-routes
        clean_methods = sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))
        if not clean_methods:
            continue
        if rule.rule.startswith("/static"):
            continue

        routes.append({"rule": rule.rule, "methods": clean_methods})

    # Group by first path segment (e.g., /api/accounts)
    grouped = {}
    for r in routes:
        seg = r["rule"].split("/")
        group = "/" + (seg[1] if len(seg) > 1 else "")
        grouped.setdefault(group, []).append(r)

    return grouped


@docs.route("/api/docs", methods=["GET"])
def api_docs():
    """Render the HTML documentation page showing grouped routes."""
    grouped = _collect_routes()
    return render_template_string(HTML_TEMPLATE, grouped=grouped)


@docs.route("/api/docs.json", methods=["GET"])
def api_docs_json():
    """Return grouped route metadata as a JSON payload."""
    grouped = _collect_routes()
    return jsonify(grouped)
