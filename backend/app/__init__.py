import os
from pathlib import Path

# must run before camel_tools is imported: its catalogue reads this at import time
_bundled = Path(__file__).resolve().parent.parent / "camel_data"
if _bundled.is_dir():
    os.environ.setdefault("CAMELTOOLS_DATA", str(_bundled))
