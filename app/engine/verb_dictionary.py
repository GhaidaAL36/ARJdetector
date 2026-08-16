import arramooz.arabicdictionary

_verb_dictionary = None


def _get_verb_dictionary():
    global _verb_dictionary
    if _verb_dictionary is None:
        _verb_dictionary = arramooz.arabicdictionary.ArabicDictionary("verbs")
    return _verb_dictionary


def lookup_verbs_by_root(root_candidates):
    cursor = _get_verb_dictionary().cursor
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


def is_transitive_verb(verb, force_intransitive_verbs=None):
    if verb in (force_intransitive_verbs or []):
        return False

    cursor = _get_verb_dictionary().cursor
    cursor.execute("SELECT transitive FROM verbs WHERE unvocalized=?", (verb,))
    rows = [row[0] for row in cursor.fetchall()]
    if not rows:
        return None
    return any(rows)
