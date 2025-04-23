
from app.models import Category
from app.extensions import db

def upsert_categories_from_plaid_data(data: dict) -> int:
    """
    Inserts or updates categories from Plaid API response data.
    Maintains a hierarchy of primary and detailed categories.
    Returns the number of new categories added.
    """
    count = 0
    for cat in data.get("categories", []):
        hierarchy = cat.get("hierarchy", [])
        plaid_cat_id = cat.get("category_id")
        if not plaid_cat_id:
            continue

        if len(hierarchy) == 1:
            primary_name = hierarchy[0]
            existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
            if not existing:
                new_primary = Category(
                    plaid_category_id=plaid_cat_id + "_primary",
                    primary_category=primary_name,
                    detailed_category=None,
                    display_name=primary_name,
                    parent_id=None,
                )
                db.session.add(new_primary)
                db.session.flush()
                count += 1

        elif len(hierarchy) >= 2:
            primary_name = hierarchy[0]
            detailed_name = hierarchy[1]

            parent = Category.query.filter_by(display_name=primary_name, parent_id=None).first()
            if not parent:
                parent = Category(
                    plaid_category_id=f"{plaid_cat_id}_primary",
                    primary_category=primary_name,
                    display_name=primary_name,
                )
                db.session.add(parent)
                db.session.flush()

            existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
            if not existing:
                new_cat = Category(
                    plaid_category_id=plaid_cat_id,
                    primary_category=primary_name,
                    detailed_category=detailed_name,
                    display_name=detailed_name,
                    parent_id=parent.id,
                )
                db.session.add(new_cat)
                count += 1

    db.session.commit()
    return count
