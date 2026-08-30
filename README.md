# ARJ Detector

A rule-based detector for Arabic stylistic redundancy — **العَرَنْجِيَّة**: phrasing
that comes from over-literal English→Arabic translation, where more natural
Arabic already exists.

It reads a sentence, finds the redundant construction, and says what to use
instead.

| construction | example | more natural |
|---|---|---|
| `بشكل` + descriptor | بشكل رسمي | رسميًا |
| `تمّ` + مصدر | تم إغلاق الباب | أُغلق البابُ |
| `قام بـ` + مصدر | قام الباحث بدراسة الظاهرة | درس الباحثُ الظاهرةَ |

## How it decides

Every flag is **deterministic and explainable**. The tool reads a sentence's
structure — parts of speech, prefixes, word order — through a morphological
analyser, checks it against a small set of stored rules and lists, and reaches a
verdict that can always be traced back to a specific check.

**No language model is asked to judge anything at request time.** There is no
inference, no scoring, no threshold. The same sentence always gets the same
answer, and any flag can be explained by pointing at the rule that produced it.

The rules are conservative in one direction on purpose: the tool would rather
flag something you disagree with than stay silent about real عرنجية. A false
flag is visible and you can argue with it; a missed one is invisible and you
never learn the tool had something to say.

## What it cannot do

Some Arabic distinctions are about **meaning**, not structure, and two sentences
that mean different things can look identical to the analyser:

```
قام الأب برعاية أبنائه       ← fine: the father shoulders a responsibility
قام الباحث بدراسة الظاهرة    ← redundant: the researcher simply did something
```

Same shape, opposite verdicts, and Arabic does not mark the difference anywhere
a program can read. Cases like these are handled by short, hand-checked lists
that grow only when a real sentence is seen judged wrongly — never by trying to
enumerate the language. `CLAUDE.md` records which lists exist, what each one is
for, and what has been tried and ruled out.

## Requirements

- Python 3.12+
- pip, and a virtual environment (recommended)

## Installation

```bash
git clone https://github.com/GhaidaAL36/ARJdetector
cd ARJdetector
python -m venv .venv
```

Activate it — `source .venv/bin/activate` on Linux/macOS/WSL, or
`.venv\Scripts\Activate.ps1` on Windows PowerShell — then:

```bash
pip install -r requirements.txt
camel_data -i morphology-db-msa-r13
camel_data -i disambig-mle-calima-msa-r13
```

The Arabic dictionary (`arramooz-pysqlite`) ships its database through pip, so
it needs no extra download.

## Running

```bash
python run.py          # or: uvicorn app.main:app --reload
```

Available at `http://127.0.0.1:8000`, with API docs at `/docs` and `/redoc`.

## Usage

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "قام الباحث بدراسة الظاهرة"}'
```

The response always has the same shape, so a client never branches on the type:

```json
{
  "flagged": true,
  "matches": [
    {
      "rule": "قام بـ",
      "flagged_phrase": "قام بدراسة",
      "explanation": "فعل مساعد زائد",
      "suggestion": "يمكن استبدال «قام بـ» بالفعل المباشر"
    }
  ]
}
```

Clean text returns the same keys with an empty list. `rule` names which rule
produced each match, and matches come back in reading order, so a sentence
containing more than one is reported in the order the phrases appear.

Diacritics are optional — the analyser supplies its own, so «تَمَّ إغلاقُ البابِ»
and «تم إغلاق الباب» give the same result.

## Trying your own sentences

To check a batch without starting the server:

```bash
python scripts/try_sentences.py doc/my_sentences.txt
```

One sentence per line; blank lines and `#` comments are skipped. Give it a CSV
with `sentence` and `expected` columns and it scores the run, reporting missed
عرنجية and false flags separately. `--out results.csv` saves the results,
`--url` sends them to a running server instead.

## Project structure

```text
app/
├── engine/
│   ├── tags.py           # the analyser's vocabulary — pure data
│   ├── analysis.py       # CAMeL Tools access
│   ├── morphology.py     # measures, roots, verb shapes
│   ├── dictionary.py     # Arramooz access
│   ├── derivation.py     # مصدر → base verb, with a confidence policy
│   ├── rule.py           # the rule predicates
│   ├── match.py          # response shape
│   └── rule_engine.py    # analyze() — runs the rules and merges matches
├── text/                 # tokenisation and lookup-key normalisation
├── rules/                # JSON reader
├── config.py  main.py  schemas.py
data/
├── rules.json            # trigger configuration
└── whitelist.json        # the stored lists
doc/                      # labelled sentence sets, used by the tests
scripts/                  # helper tools, never imported by the app
```

Dependencies run one way with no cycles, and each external dependency has
exactly one home — CAMeL Tools in `analysis.py`, Arramooz in `dictionary.py` —
so both are single mocking boundaries in the tests.

## Configuration

Both files in `data/` are editable without touching Python. `rules.json` holds
the trigger configuration for each rule; removing a rule's block disables that
rule. `whitelist.json` holds the stored lists — each one exists to correct a
known, finite gap, and each is capped and tested to keep it that way.

## Tests

```bash
pytest
```

Pure unit tests, tests mocked at the CAMeL and Arramooz boundaries, and
integration tests against the real analyser and dictionary. Some read the
labelled sentence sets in `doc/`, so those files are part of the suite rather
than documentation.
