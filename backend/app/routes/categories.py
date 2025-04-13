
from sqlalchemy.orm import aliased
from flask import Blueprint, jsonify
from app.models import Category
from app import db, plaid_client
import logging

logger = logging.getLogger(__name__)

categories = Blueprint("categories", __name__)

@categories.route("/tree", methods=["GET"])
def get_category_tree():
    tree = {}
    categories = Category.query.all()
    for cat in categories:
        primary = cat.primary_category or "Unknown"
        detailed = cat.detailed_category or cat.display_name or "Other"

        if primary not in tree:
            tree[primary] = []

        tree[primary].append({
            "name": detailed,
            "id": cat.id,
            "plaid_id": cat.plaid_category_id
        })

    nested = [{"name": k, "children": v} for k, v in tree.items()]
    return jsonify({"status": "success", "data": nested})


categories.route("/refresh", methods=["POST"])
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
                existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
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
                parent = db.session.query(Category).join(
                    ParentCategory, Category.parent_id == ParentCategory.id
                ).filter(ParentCategory.display_name == primary).first()

                if not parent:
                    parent = Category(
                        plaid_category_id=f"{plaid_cat_id}_primary",
                        primary_category=primary,
                        display_name=primary
                    )
                    db.session.add(parent)
                    db.session.flush()

                existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
                if not existing:
                    child = Category(
                        plaid_category_id=plaid_cat_id,
                        primary_category=primary,
                        detailed_category=detailed,
                        display_name=detailed,
                        parent_id=parent.id
                    )
                    db.session.add(child)

        db.session.commit()
        logger.info("✅ Refreshed Plaid categories using SDK")
        return jsonify({"status": "success", "message": "Categories refreshed"})

    except Exception as e:
        logger.error(f"❌ Failed to refresh Plaid categories: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

