"""Arbitrage dashboard endpoints."""

from __future__ import annotations

import json
import os

from app.config.constants import ARBITRAGE_FILE
from flask import Blueprint, jsonify

arbitrage = Blueprint("arbitrage", __name__)


@arbitrage.route("/current", methods=["GET"])
def get_current_arbitrage():
    """Return the latest R/S arbitrage snapshot.

    The Discord bot writes periodic updates to :data:`ARBITRAGE_FILE`.
    If the file contains JSON, it is returned as-is. Otherwise the raw
    text content is wrapped under the ``content`` key.
    """

    if os.path.exists(ARBITRAGE_FILE):
        try:
            with open(ARBITRAGE_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError:
            with open(ARBITRAGE_FILE, "r", encoding="utf-8") as fh:
                data = {"content": fh.read()}
    else:
        data = {"content": ""}

    return jsonify(data), 200
