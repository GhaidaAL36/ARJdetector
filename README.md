# ARJ Detector


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
│   └── main.py
├── data/
│   └── rules.json
├── test/
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
