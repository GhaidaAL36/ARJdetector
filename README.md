# ARJ Detector

Rule-based Arabic stylistic redundancy detector, targeting "Aranjiyyah"
(العَرَنْجِيَّة) — overuse of `بشكل + adjective` constructions where a direct
adverb or مفعول مطلق would be more natural Arabic (e.g. "بشكل رسمي" → "رسمياً").

## Project Structure

```text
ARJdetector/
├── app/
│   ├── engine/
│   │   ├── match.py
│   │   ├── rule.py
│   │   └── rule_engine.py
│   ├── rules/
│   │   └── rule_loader.py
│   ├── text/
│   │   └── preprocessor.py
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── data/
│   ├── rules.json
│   └── whitelist.json
├── tests/
├── run.py
├── requirements.txt
└── README.md
```

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

## Running Tests

```bash
pytest tests/
```
