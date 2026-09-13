# -*- coding: utf-8 -*-
"""The deploy excludes packages that camel_tools declares but never uses.

pyproject.toml overrides torch, transformers, camel-kenlm, numpy, pandas, scipy
and scikit-learn out of the Vercel install — that is what keeps the function
under its size limit. Nothing stops a later change from importing one of them,
and the local venv has them all installed, so such a change would pass every
other test here and fail only after deploying, with an ImportError. This one
fails first.
"""
import json
import subprocess
import sys
import tomllib
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

IMPORT_NAMES = {"scikit-learn": "sklearn", "camel-kenlm": "kenlm"}

PROBE = """
import json, sys
from app.config import rules_path, whitelist_path
from app.engine.rule_engine import analyze
result = analyze(rules_path, whitelist_path,
    "تم إطلاق المنصة بشكل رسمي من قبل المشرف وقام الفريق بدراسة الظاهرة")
print(json.dumps({
    "rules": sorted({match["rule"] for match in result["matches"]}),
    "modules": sorted({name.split(".")[0] for name in sys.modules}),
}))
"""


def excluded_modules():
    config = tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))
    specs = config["tool"]["uv"]["override-dependencies"]
    names = [spec.split(";")[0].strip() for spec in specs]
    return {IMPORT_NAMES.get(name, name.replace("-", "_")) for name in names}


def test_the_exclusion_list_is_read_from_pyproject():
    # guards the test below against passing vacuously on a parsing mistake
    assert {"torch", "numpy", "sklearn"} <= excluded_modules()


def test_a_real_analysis_never_imports_a_package_the_deploy_excludes():
    # fresh interpreter: other tests in this session may have imported numpy
    completed = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(completed.stdout.strip().splitlines()[-1])

    assert report["rules"] == sorted(["بشكل", "تم", "قام بـ", "من قبل"])
    assert not set(report["modules"]) & excluded_modules()
