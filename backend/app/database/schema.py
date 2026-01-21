from sqlalchemy import text


def ensure_schema(engine, schema: str):
    if schema == "public":
        raise RuntimeError(
            "Refusing to create or modify schema 'public' programmatically"
        )

    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
