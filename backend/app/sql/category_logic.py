from app.extensions import db
from app.models import Category
from sqlalchemy.exc import IntegrityError


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
        if not plaid_cat_id or not hierarchy:
            continue

        primary_name = hierarchy[0]
        detailed_name = hierarchy[1] if len(hierarchy) > 1 else None
        display_name = (
            f"{primary_name} > {detailed_name}" if detailed_name else primary_name
        )

        # Ensure parent exists (or is created)
        parent = None
        if detailed_name:
            parent = Category.query.filter_by(
                primary_category=primary_name, detailed_category=None, parent_id=None
            ).first()
            if not parent:
                parent = Category(
                    plaid_category_id=f"{plaid_cat_id}_primary",
                    primary_category=primary_name,
                    detailed_category=None,
                    display_name=primary_name,
                    parent_id=None,
                )
                db.session.add(parent)
                db.session.flush()

        # Check for existing category by Plaid category ID
        existing = Category.query.filter_by(plaid_category_id=plaid_cat_id).first()
        if not existing:
            new_cat = Category(
                plaid_category_id=plaid_cat_id,
                primary_category=primary_name,
                detailed_category=detailed_name,
                display_name=display_name,
                parent_id=parent.id if parent else None,
            )
            db.session.add(new_cat)
            count += 1

    db.session.commit()
    return count


def resolve_or_create_category(category_path, plaid_category_id=None):
    primary = category_path[0] if len(category_path) > 0 else "Uncategorized"
    detailed = category_path[1] if len(category_path) > 1 else None

    # Prevent duplicate insert before attempting
    existing = Category.query.filter_by(
        primary_category=primary, detailed_category=detailed
    ).first()
    if existing:
        return existing

    # Ensure parent exists if needed
    parent = None
    if detailed:
        parent = Category.query.filter_by(
            primary_category=primary, detailed_category=None
        ).first()
        if not parent:
            parent = Category(
                plaid_category_id=(
                    f"{plaid_category_id}_parent" if plaid_category_id else None
                ),
                primary_category=primary,
                detailed_category=None,
                display_name=primary,
                parent_id=None,
            )
            db.session.add(parent)
            db.session.flush()

    # Safe insert with fallback
    try:
        category = Category(
            plaid_category_id=plaid_category_id,
            primary_category=primary,
            detailed_category=detailed,
            display_name=f"{primary} > {detailed}" if detailed else primary,
            parent_id=parent.id if parent else None,
        )
        db.session.add(category)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        category = Category.query.filter_by(
            primary_category=primary, detailed_category=detailed
        ).first()

    return category
