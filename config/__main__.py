"""Check the settings file: .venv/bin/python -m config"""

from datetime import time

from config.settings_loader import load_or_exit


def show(value):
    """Print a setting the way it is written in settings.toml: times as HH:MM, lists plainly."""
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, (list, tuple)):
        return ", ".join(show(v) for v in value)
    return str(value)


settings = load_or_exit()
print("Settings OK.")
for section, items in settings.as_dict().items():
    for key, value in items.items():
        print(f"  [{section}] {key} = {show(value)}")
