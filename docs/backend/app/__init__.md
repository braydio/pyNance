## 📘 `__init__.py`
```markdown
# Application Factory

Initializes the Flask application. Sets up CORS, loads configuration, initializes
SQLAlchemy and migrations, then registers all route blueprints. The
`create_app()` function returns a configured `Flask` instance used by `run.py`
and the CLI tools. CLI commands like `sync-accounts` are attached here and the
available routes are logged on startup.

**Dependencies**: `Flask`, `flask_cors`, `flask_migrate`, `app.config`,
`app.extensions`, various route modules.
```
