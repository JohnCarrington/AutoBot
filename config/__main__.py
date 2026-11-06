"""Check the settings file: .venv/bin/python -m config"""

from config.settings_loader import load_or_exit

settings = load_or_exit()
print("Settings OK.")
for section, items in settings.as_dict().items():
    for key, value in items.items():
        print(f"  [{section}] {key} = {value}")
