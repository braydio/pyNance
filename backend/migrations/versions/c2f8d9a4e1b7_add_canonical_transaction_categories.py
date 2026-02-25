"""Add canonical category slug/display fields and backfill existing rows.

Revision ID: c2f8d9a4e1b7
Revises: 9d3f4c21a7b9
Create Date: 2026-02-25
"""

from __future__ import annotations

import re

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c2f8d9a4e1b7"
down_revision = "9d3f4c21a7b9"
branch_labels = None
depends_on = None


def _normalize_slug(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized.upper()


def _humanize(value: str) -> str:
    return value.replace("_", " ").lower().title().replace(" And ", " and ")


def _canonicalize(
    primary: str | None,
    detailed: str | None,
    pfc_primary: str | None,
    pfc_detailed: str | None,
) -> tuple[str, str]:
    unknown = "UNKNOWN"
    np_primary = _normalize_slug(pfc_primary)
    np_detailed = _normalize_slug(pfc_detailed)
    if np_detailed and np_detailed != unknown:
        slug = np_detailed
        display = _humanize(np_primary or unknown)
        if slug != (np_primary or ""):
            suffix = (
                slug[len(np_primary) + 1 :]
                if np_primary and slug.startswith(f"{np_primary}_")
                else slug
            )
            display = f"{display} - {_humanize(suffix)}"
        return slug, display

    legacy_primary = _normalize_slug(primary)
    legacy_detailed = _normalize_slug(detailed)
    if legacy_detailed and legacy_detailed != unknown:
        slug = legacy_detailed
        if legacy_primary and not slug.startswith(f"{legacy_primary}_"):
            slug = f"{legacy_primary}_{slug}"
        display = _humanize(legacy_primary or slug)
        if legacy_primary and slug.startswith(f"{legacy_primary}_"):
            display = f"{_humanize(legacy_primary)} - {_humanize(slug[len(legacy_primary) + 1 :])}"
        elif not legacy_primary:
            display = _humanize(slug)
        return slug, display

    if legacy_primary and legacy_primary != unknown:
        return legacy_primary, _humanize(legacy_primary)

    return unknown, "Unknown"


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "categories", sa.Column("category_slug", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "categories",
        sa.Column("category_display", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "transactions", sa.Column("category_slug", sa.String(length=128), nullable=True)
    )
    op.add_column(
        "transactions",
        sa.Column("category_display", sa.String(length=256), nullable=True),
    )

    categories = (
        bind.execute(
            sa.text(
                """
            SELECT id, primary_category, detailed_category, pfc_primary, pfc_detailed
            FROM categories
            ORDER BY id
            """
            )
        )
        .mappings()
        .all()
    )

    keepers: dict[str, int] = {}
    duplicates: list[tuple[int, int]] = []

    for row in categories:
        slug, display = _canonicalize(
            row["primary_category"],
            row["detailed_category"],
            row["pfc_primary"],
            row["pfc_detailed"],
        )
        bind.execute(
            sa.text(
                """
                UPDATE categories
                SET category_slug = :slug,
                    category_display = :display
                WHERE id = :category_id
                """
            ),
            {"slug": slug, "display": display, "category_id": row["id"]},
        )
        keeper = keepers.setdefault(slug, row["id"])
        if keeper != row["id"]:
            duplicates.append((row["id"], keeper))

    for duplicate_id, keeper_id in duplicates:
        bind.execute(
            sa.text(
                "UPDATE transactions SET category_id = :keeper_id WHERE category_id = :duplicate_id"
            ),
            {"keeper_id": keeper_id, "duplicate_id": duplicate_id},
        )
        bind.execute(
            sa.text("DELETE FROM categories WHERE id = :duplicate_id"),
            {"duplicate_id": duplicate_id},
        )

    bind.execute(
        sa.text(
            """
            UPDATE transactions AS t
            SET category_slug = c.category_slug,
                category_display = COALESCE(c.category_display, t.category, 'Uncategorized')
            FROM categories AS c
            WHERE t.category_id = c.id
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE transactions
            SET category_slug = COALESCE(category_slug, 'UNCATEGORIZED'),
                category_display = COALESCE(category_display, category, 'Uncategorized')
            """
        )
    )

    op.create_index(
        "ix_categories_category_slug", "categories", ["category_slug"], unique=True
    )
    op.create_index(
        "ix_transactions_category_slug", "transactions", ["category_slug"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_category_slug", table_name="transactions")
    op.drop_index("ix_categories_category_slug", table_name="categories")
    op.drop_column("transactions", "category_display")
    op.drop_column("transactions", "category_slug")
    op.drop_column("categories", "category_display")
    op.drop_column("categories", "category_slug")
