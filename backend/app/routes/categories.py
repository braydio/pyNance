"""Category management endpoints."""

import logging

from app import db, plaid_client
from app.models import Category
from flask import Blueprint, jsonify
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)

categories = Blueprint("categories", __name__)


@categories.route("/tree", methods=["GET"])
def get_category_tree():
    """Return categories grouped by primary category.

    Each root node contains a unique ``id`` and ``label`` so the frontend
    dropdown can correctly track selections. Children retain their database
    identifiers and Plaid mapping.
    """

    grouped: dict[str, list[dict]] = {}
    rows = Category.query.all()
    for cat in rows:
        primary = cat.primary_category or "Unknown"
        detailed = cat.detailed_category or cat.display_name or "Other"

        if primary not in grouped:
            grouped[primary] = []

        grouped[primary].append(
            {"id": cat.id, "label": detailed, "plaid_id": cat.plaid_category_id}
        )

    nested = [
        {"id": idx + 1, "label": label, "children": children}
        for idx, (label, children) in enumerate(grouped.items())
    ]
    return jsonify({"status": "success", "data": nested})


@categories.route("/refresh", methods=["POST"])
def refresh_plaid_categories():
    try:
        response = plaid_client.categories_get({})
        categories = response.to_dict().get("categories", [])

        for cat in categories:
            hierarchy = cat.get("hierarchy", [])
            plaid_cat_id = cat.get("category_id")

            if not plaid_cat_id or not hierarchy:
                continue

            if len(hierarchy) == 1:
                primary = hierarchy[0]
                existing = Category.query.filter_by(
                    plaid_category_id=plaid_cat_id
                ).first()
                if not existing:
                    parent = Category(
                        plaid_category_id=plaid_cat_id,
                        primary_category=primary,
                        display_name=primary,
                        detailed_category=None,
                        parent_id=None,
                    )
                    db.session.add(parent)
                    db.session.flush()

            elif len(hierarchy) >= 2:
                primary = hierarchy[0]
                detailed = hierarchy[1]

                ParentCategory = aliased(Category)
                parent = (
                    db.session.query(Category)
                    .join(ParentCategory, Category.parent_id == ParentCategory.id)
                    .filter(ParentCategory.display_name == primary)
                    .first()
                )

                if not parent:
                    parent = Category(
                        plaid_category_id=f"{plaid_cat_id}_primary",
                        primary_category=primary,
                        display_name=primary,
                    )
                    db.session.add(parent)
                    db.session.flush()

                existing = Category.query.filter_by(
                    plaid_category_id=plaid_cat_id
                ).first()
                if not existing:
                    child = Category(
                        plaid_category_id=plaid_cat_id,
                        primary_category=primary,
                        detailed_category=detailed,
                        display_name=detailed,
                        parent_id=parent.id,
                    )
                    db.session.add(child)

        db.session.commit()
        logger.info("✅ Refreshed Plaid categories using SDK")
        return jsonify({"status": "success", "message": "Categories refreshed"})

    except Exception as e:
        logger.error(f"❌ Failed to refresh Plaid categories: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
