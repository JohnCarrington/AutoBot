import sys
from pathlib import Path

# Let tests import the project's parts (config, prices, ...) from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
