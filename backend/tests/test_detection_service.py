import json
from pathlib import Path

from app.schemas.detection import TrafficRecord
from app.services.detection_service import detect, extract_features, load_artifacts
from app.services.explanation_service import explain_detection


def test_extract_features_counts_request_values(traffic_record):
    features = extract_features(TrafficRecord.model_validate(traffic_record))

    assert features["endpoint_depth"] == 2
    assert features["query_param_count"] == 1
    assert features["status_code"] == 200
    assert features["is_error_status"] == 0


def test_detect_flags_sql_pattern(traffic_record):
    traffic_record["request"]["url"] = "https://example.com/search?q=' OR 1=1 --"
    result = detect(TrafficRecord.model_validate(traffic_record))

    assert result["features"]["sql_pattern_score"] == 1
    assert result["attack_type"] == "SQL Injection"
    assert 0 <= result["anomaly_score"] <= 1
    assert "decision threshold" in result["explanation"]
    assert "SQL keywords" in result["explanation"]


def test_explanation_describes_score_distance():
    features = {
        "sql_pattern_score": 1,
        "xss_pattern_score": 0,
        "traversal_pattern_score": 0,
        "command_pattern_score": 0,
        "log_injection_pattern_score": 0,
        "log4j_pattern_score": 0,
        "cookie_injection_pattern_score": 0,
        "is_error_status": 0,
    }

    reasons, explanation = explain_detection(
        features,
        suspicious=True,
        score=0.6188,
        threshold=0.5752,
    )

    assert reasons == [
        "SQL keywords, operators, or comment syntax were detected in the request"
    ]
    assert "0.0436 above" in explanation


def test_saved_model_matches_notebook_verification_samples():
    records = json.loads(Path("datasets/dataset_3_train.json").read_text())
    samples = [records[0], records[1], records[2]]
    for record in records:
        if record.get("request", {}).get("Attack_Tag") and len(samples) < 6:
            samples.append(record)

    expected_scores = [0.5176, 0.6188, 0.3627, 0.6188, 0.6451, 0.6226]
    scores = [detect(TrafficRecord.model_validate(record))["anomaly_score"] for record in samples]

    assert scores == expected_scores


def test_saved_model_artifacts_are_complete():
    config, model = load_artifacts()

    assert len(model["trees"]) == model["n_trees"] == 300
    assert model["threshold"] == config["threshold"] == 0.5752
    assert len(config["feature_names"]) == 21
    assert len(config["min_values"]) == len(config["max_values"]) == 21
    assert len(model["feature_weights"]) == 21
