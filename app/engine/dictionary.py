import arramooz.arabicdictionary

_dictionary = None


def _get_dictionary():
    global _dictionary
    if _dictionary is None:
        _dictionary = arramooz.arabicdictionary.ArabicDictionary("verbs")
    return _dictionary


def lookup_verbs_by_root(root_candidates):
    cursor = _get_dictionary().cursor
    rows = []
    seen = set()

    for root in root_candidates:
        cursor.execute(
            "SELECT unvocalized, vocalized, root, transitive FROM verbs "
            "WHERE root = ? OR root LIKE ? OR root LIKE ? OR root LIKE ?",
            (root, f"{root};%", f"%;{root}", f"%;{root};%"),
        )
        for row in cursor:
            row = dict(row)
            key = (row["unvocalized"], row["vocalized"])
            if key not in seen:
                seen.add(key)
                rows.append(row)

    return rows


def is_masdar(word, force_not_masdar=None):
    candidates = [word]
    if word.startswith("ال"):
        candidates.append(word[2:])

    if force_not_masdar and any(c in force_not_masdar for c in candidates):
        return False

    cursor = _get_dictionary().cursor
    rows = []
    for candidate in candidates:
        cursor.execute(
            "SELECT wordtype, category FROM nouns WHERE unvocalized=?", (candidate,)
        )
        rows.extend(dict(row) for row in cursor.fetchall())

    if not rows:
        return None
    return any(
        "مصدر" in (row.get("category") or "") or "مصدر" in (row.get("wordtype") or "")
        for row in rows
    )


def is_transitive_verb(verb, force_intransitive_verbs=None):
    if verb in (force_intransitive_verbs or []):
        return False

    cursor = _get_dictionary().cursor
    cursor.execute("SELECT transitive FROM verbs WHERE unvocalized=?", (verb,))
    rows = [row[0] for row in cursor.fetchall()]
    if not rows:
        return None
    return any(rows)
