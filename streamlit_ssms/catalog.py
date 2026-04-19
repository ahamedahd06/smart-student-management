"""
Programme / module names for registration, lecturer sessions, and admin forms.
(`module_code` in the DB stores the same display string — no separate short codes.)
"""
from __future__ import annotations

PROGRAMMES: list[str] = [
    "Software Engineering",
    "Cyber Security",
    "Data Science",
    "Computer Science",
    "Fashion Design",
]

OTHER_OPTION = "Other (specify below)"


def all_programme_choices() -> list[str]:
    return PROGRAMMES + [OTHER_OPTION]
