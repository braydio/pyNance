"""Persistent application-wide settings."""

from app.extensions import db

from .mixins import TimestampMixin


class LlmSettings(db.Model, TimestampMixin):
    """Configuration for the dashboard's optional LLM-generated message."""

    __tablename__ = "llm_settings"

    id = db.Column(db.Integer, primary_key=True)
    custom_message_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default=db.text("true"),
    )
    base_url = db.Column(db.String(2048), nullable=True)
