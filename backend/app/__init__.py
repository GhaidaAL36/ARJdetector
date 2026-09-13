import os
import tempfile
from pathlib import Path

# both of these must run before camel_tools is imported.
#
# camel_tools creates ~/.camel_tools at import time, before it ever reads
# CAMELTOOLS_DATA — so on a read-only home (Vercel) the import itself crashes.
# Trying the same mkdir first, and moving HOME somewhere writable only if it
# fails, leaves local development untouched.
try:
    (Path.home() / ".camel_tools").mkdir(parents=True, exist_ok=True)
except OSError:
    os.environ["HOME"] = tempfile.gettempdir()

_bundled = Path(__file__).resolve().parent.parent / "camel_data"
if _bundled.is_dir():
    os.environ.setdefault("CAMELTOOLS_DATA", str(_bundled))
