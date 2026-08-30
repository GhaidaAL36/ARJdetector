# -*- coding: utf-8 -*-
"""Access to the labelled sentence sets in doc/.

Those files are gitignored — they are Ghaida's own sentences. Everything that
reads them goes through here, so a checkout without them still collects and
runs: the affected tests skip with a clear reason instead of erroring.
"""
import csv
import io
import os

import pytest

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doc")


def rows(name):
    """Every row of doc/<name>, or [] when the file is not present."""
    path = os.path.join(DOC, name)
    if not os.path.exists(path):
        return []
    with io.open(path, encoding="utf-8-sig") as handle:
        return [r for r in csv.DictReader(handle)]


def needs(name):
    """Module-level marker: skip when the labelled set is not checked out."""
    return pytest.mark.skipif(
        not os.path.exists(os.path.join(DOC, name)),
        reason=f"doc/{name} not present (gitignored local sentence set)",
    )
