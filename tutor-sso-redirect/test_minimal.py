class MockHooks:
    class Filters:
        class ENV_PATCHES:
            @staticmethod
            def add_items(items):
                pass

hooks = MockHooks()

# This should be the exact same syntax
hooks.Filters.ENV_PATCHES.add_items([
    ("openedx-lms-common-settings", """# SSO Redirect Plugin Settings
Test content
"""),
])

print("Syntax works!")