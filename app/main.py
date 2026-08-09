from fastapi import FastAPI
from app.engine.rule_engine import analyze
from app.schemas import AnalyzeRequest
from app.config import rules_path, whitelist_path

app = FastAPI()

@app.post("/analyze")
def analyze_endpoint(request: AnalyzeRequest):
    result = analyze(rules_path, whitelist_path, request.text)
    return result
