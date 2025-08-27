#!/usr/bin/env python3
# Test the syntax structure

from tutor import hooks

hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings", """
# Test content
print("test")
"""),
])

print("Syntax OK")