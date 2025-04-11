
from flask import Blueprint, jsonify
from app.models import Category

categories = Blueprint("categories", __name__)

@categories.route("/tree", methods=["GET"])
def get_category_tree():
    """
    Returns a nested category tree:
    [
      {
        "name": "Food and Drink",
        "children": [
          { "name": "Restaurants", "id": 3, "plaid_id": "13005000" },
          ...
        ]
      },
      ...
    ]
    """
    tree = {}
    categories = Category.query.all()
    for cat in categories:
        primary = cat.primary_category or "Unknown"
        detailed = cat.detailed_category or "Other"

        if primary not in tree:
            tree[primary] = []

        tree[primary].append({
            "name": detailed,
            "id": cat.id,
            "plaid_id": cat.plaid_category_id
        })

    # Convert to a list of nested dicts
    nested = [{"name": parent, "children": children} for parent, children in tree.items()]
    return jsonify({"status": "success", "data": nested})
