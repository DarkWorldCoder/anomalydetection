from __future__ import annotations

import json
import math
import pickle
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from app.schemas.detection import TrafficRecord
from app.services.explanation_service import explain_detection

ROOT = Path(__file__).resolve().parents[2]
SPECIAL_CHARS = "'\"<>=;(){}[]$|&\\/:%"
PATTERNS = {
    "SQL Injection": re.compile(
        r"(\b(union\s+select|select\s+.*\s+from|insert\s+into|delete\s+from|drop\s+table|information_schema|benchmark\s*\(|sleep\s*\(|from\s+employees|limit\s+\d+|where\s+|or\s+|and\s+)\b|'\s*or\s*'|'\s*or\s*1\s*=\s*1|(\s--|--\s|;\s*--|'--|\"--|--$)|;\s*select)",
        re.I,
    ),
    "Cross Site Scripting": re.compile(
        r"(<script.*?>|alert\s*\(|onerror\s*=|onload\s*=|document\.cookie|javascript:|<iframe>|<svg|<body|img\s+src=)", re.I
    ),
    "Directory Traversal": re.compile(r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.\.%2f|windows\.ini|/etc/passwd|win\.ini|boot\.ini)", re.I),
    "Remote Code Execution": re.compile(r"(\b(whoami|powershell|os\.system|builtins|subprocess|cmd\.exe|cat\s+/etc)\b)", re.I),
    "Log Injection": re.compile(r"(%0a|%0d|\\n|\\r|\n|\r).*(signin:|error:|admin|user)", re.I),
    "Log4j": re.compile(r"(\$\{jndi:(ldap|rmi|dns)|jndi:(ldap|rmi|dns))", re.I),
    "Cookie Injection": re.compile(r"(gASV[A-Za-z0-9+/=]{10,}|builtins|__main__|pickle|namedtuple|cposix|eval\(|exec\(|import\s+os|powershell)", re.I),
}


@lru_cache
def load_artifacts() -> tuple[dict, dict]:
    config = json.loads((ROOT / "storage/feature_config.json").read_text())
    with (ROOT / config["model_file"]).open("rb") as file:
        model = pickle.load(file)
    return config, model


def extract_features(record: TrafficRecord) -> dict[str, float | int]:
    request = record.request
    response = record.response
    parsed = urlparse(request.url)
    endpoint = parsed.path or "/"
    cookie = f'{request.headers.get("Cookie", "")} {request.headers.get("Set-Cookie", "")}'
    headers_text = unquote(str(request.headers))
    url_body = unquote(f"{request.url} {request.body}").lower()
    combined = " ".join(
        [unquote(request.url), endpoint, unquote(parsed.query), headers_text, request.body, response.body]
    ).lower()
    hits = {name: float(bool(pattern.search(headers_text if name == "Log4j" else cookie if name == "Cookie Injection" else combined if name == "Remote Code Execution" else url_body))) for name, pattern in PATTERNS.items()}
    special_count = sum(combined.count(char) for char in SPECIAL_CHARS)
    total_length = len(request.url) + len(request.body) + len(cookie) + 1

    return {
        "url_length": len(request.url),
        "endpoint_depth": len([part for part in endpoint.split("/") if part]),
        "query_param_count": len(parse_qs(parsed.query)),
        "body_length": len(request.body),
        "header_count": len(request.headers),
        "cookie_length": len(cookie),
        "user_agent_length": len(str(request.headers.get("User-Agent", ""))),
        "special_char_count": special_count,
        "special_char_density": special_count / total_length,
        "sql_pattern_score": hits["SQL Injection"],
        "xss_pattern_score": hits["Cross Site Scripting"],
        "traversal_pattern_score": hits["Directory Traversal"],
        "command_pattern_score": hits["Remote Code Execution"],
        "log_injection_pattern_score": hits["Log Injection"],
        "log4j_pattern_score": hits["Log4j"],
        "cookie_injection_pattern_score": hits["Cookie Injection"],
        "composite_anomaly_score": sum(hits.values()),
        "response_body_length": len(response.body),
        "response_header_count": len(response.headers),
        "status_code": response.status_code,
        "is_error_status": int(response.status_code >= 400),
    }


def average_path_length(size: int) -> float:
    if size <= 1:
        return 0
    if size == 2:
        return 1
    return 2 * (math.log(size - 1) + 0.5772156649) - 2 * (size - 1) / size


def tree_path_length(vector: list[float], node: dict | None, depth: int = 0) -> float:
    if node is None:
        return depth
    if node.get("is_leaf"):
        return depth + average_path_length(node.get("size", 0))
    side = "left" if vector[node["feature_index"]] < node["split_value"] else "right"
    return tree_path_length(vector, node.get(side), depth + 1)


def detect(record: TrafficRecord) -> dict:
    config, model = load_artifacts()
    features = extract_features(record)
    raw = [float(features[name]) for name in config["feature_names"]]
    scaled = [
        (value - low) / (high - low if high != low else 1)
        for value, low, high in zip(raw, config["min_values"], config["max_values"])
    ]
    lengths = [tree_path_length(scaled, tree) for tree in model["trees"]]
    score = 2 ** (-(sum(lengths) / len(lengths)) / average_path_length(model["sample_size"]))
    suspicious = score >= config["threshold"]
    matched = [name for name, pattern in PATTERNS.items() if pattern.search(unquote(f"{record.request.url} {record.request.body} {record.request.headers}"))]
    risk = "high" if score >= 0.7 else "medium" if suspicious else "low"
    reasons, explanation = explain_detection(
        features,
        suspicious,
        score=score,
        threshold=config["threshold"],
    )

    return {
        "features": features,
        "anomaly_score": round(score, 4),
        "threshold": config["threshold"],
        "prediction": "Suspicious" if suspicious else "Benign",
        "risk_level": risk,
        "attack_type": matched[0] if matched else record.request.Attack_Tag or "Unknown",
        "reasons": reasons,
        "explanation": explanation,
    }
