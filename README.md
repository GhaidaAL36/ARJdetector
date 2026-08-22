# ARJ Detector

Rule-based Arabic stylistic redundancy detector, targeting "Aranjiyyah"
(العَرَنْجِيَّة) — patterns that come from over-literal English→Arabic
translation, where more natural Arabic exists.

Two rules are implemented, and both report through the same endpoint:

| rule | detects | example |
|------|---------|---------|
| `بشكل` | `بشكل + descriptor` where a direct adverb or مفعول مطلق is more natural | «بشكل رسمي» → «رسمياً» |
| `تم` | `تمّ/يتمّ + transitive masdar` used as a stand-in passive | «تم إغلاق الباب» → «أُغلق الباب» |

Every decision is deterministic — morphological analysis, dictionary lookups
and stored override lists. No model is asked to judge a flag at request time.

## Project Structure

```text
ARJdetector/
├── app/
│   ├── engine/
│   │   ├── analysis.py       # CAMeL Tools access (disambiguator + analyzer)
│   │   ├── morphology.py     # measures, roots, verb shapes — pure functions
│   │   ├── dictionary.py     # Arramooz access (verbs + nouns tables)
│   │   ├── derivation.py     # masdar → base verb, with a confidence policy
│   │   ├── rule.py           # rule predicates — pure, no imports
│   │   ├── match.py          # response building
│   │   └── rule_engine.py    # analyze() — orchestrates both rules
│   ├── rules/
│   │   └── rule_loader.py
│   ├── text/
│   │   └── preprocessor.py
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── data/
│   ├── rules.json            # trigger configuration
│   └── whitelist.json        # whitelists and override lists
├── tests/
├── run.py
├── requirements.txt
└── README.md
```

Dependencies run one way, with no cycles. Each external dependency has exactly
one home — CAMeL Tools in `analysis.py`, Arramooz in `dictionary.py` — so both
are single mocking boundaries in the tests.

## Requirements

- Python 3.12+
- pip
- Virtual Environment (recommended)

## Installation

Clone the repository:

```bash
git clone https://github.com/GhaidaAL36/ARJdetector
cd ARJdetector
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment.

### Linux / macOS / WSL

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Download the required CAMeL Tools data:

```bash
camel_data -i morphology-db-msa-r13
camel_data -i disambig-mle-calima-msa-r13
```

The Arabic dictionary (`arramooz-pysqlite`) ships its own database through pip,
so it needs no extra download step.

## Running the Application

Using the provided entry point:

```bash
python run.py
```

Or directly with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The application will be available at:

```
http://127.0.0.1:8000
```

## API Documentation

Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

## Usage

Send a `POST` request to `/analyze` with the text to check:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "الجو جميل بشكل رائع اليوم"}'
```

Request body:

```json
{
  "text": "الجو جميل بشكل رائع اليوم"
}
```

### Response

The response always has the same shape, whether or not anything was found, so
a client never has to branch on the type:

```json
{
  "flagged": true,
  "matches": [
    {
      "rule": "بشكل",
      "flagged_phrase": "بشكل رائع",
      "explanation": "حشو أسلوبي",
      "suggestion": "يمكن حذف «بشكل» أو استبدالها بصياغة أكثر طبيعية"
    }
  ]
}
```

Clean text returns the same keys with an empty list:

```json
{
  "flagged": false,
  "matches": []
}
```

`rule` says which rule produced the match (`بشكل` or `تم`), and matches are
returned in reading order, so a sentence containing both comes back in the
order the phrases appear in the text.

Diacritics are optional — the analyzer supplies its own, so «تَمَّ إغلاقُ
البابِ» and «تم إغلاق الباب» give the same result.

## Configuration

Both rules read their data from `data/`, editable without touching Python:

- `rules.json` — `trigger_word` for بشكل, `tam_trigger_lex` for تمّ. Removing
  `tam_trigger_lex` disables the تمّ rule entirely.
- `whitelist.json` — the whitelists and override lists. Each exists to correct
  a known, finite gap in an algorithmic mechanism rather than to act as a
  lexicon; see `CLAUDE.md` for what each one carries and why.

## Running Tests

```bash
pytest tests/
```

The suite mixes pure unit tests, tests mocked at the CAMeL and Arramooz
boundaries, and integration tests that run against the real analyzer and
dictionary.
