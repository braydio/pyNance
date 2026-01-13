def humanize_enum(value: str) -> str:
    if not value:
        return ""
    return value.replace("_", " ").lower().title().replace(" And ", " and ")


def strip_parent(child: str, parent: str) -> str:
    if not child or not parent:
        return child or ""
    prefix = f"{parent}_"
    if child.startswith(prefix):
        return child[len(prefix) :]
    return child


def category_display(primary: str, detailed: str | None) -> str:
    primary_h = humanize_enum(primary)
    if not detailed:
        return primary_h
    detailed_clean = strip_parent(detailed, primary)
    detailed_h = humanize_enum(detailed_clean)
    return f"{primary_h} - {detailed_h}"
