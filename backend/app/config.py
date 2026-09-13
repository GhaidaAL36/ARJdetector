from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

rules_path = str(DATA_DIR / "rules.json")
whitelist_path = str(DATA_DIR / "whitelist.json")
