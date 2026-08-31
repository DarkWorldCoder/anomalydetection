FEATURE_REASONS = {
    "sql_pattern_score": "SQL keywords, operators, or comment syntax were detected in the request",
    "xss_pattern_score": "Executable HTML or script syntax was detected in the request",
    "traversal_pattern_score": "Parent-directory or sensitive-file traversal syntax was detected",
    "command_pattern_score": "Operating-system command execution syntax was detected",
    "log_injection_pattern_score": "Encoded line breaks and forged log content were detected",
    "log4j_pattern_score": "A JNDI lookup associated with Log4j exploitation was detected",
    "cookie_injection_pattern_score": "Serialized or executable content was detected in a cookie",
}


def explain_detection(
    features: dict,
    suspicious: bool,
    score: float | None = None,
    threshold: float | None = None,
) -> tuple[list[str], str]:
    reasons = [message for name, message in FEATURE_REASONS.items() if features[name] > 0]
    if features["is_error_status"]:
        reasons.append("The server returned an HTTP error response")
    if suspicious and not reasons:
        reasons.append("The combined request measurements differ from the traffic learned by the model")

    if score is not None and threshold is not None:
        distance = abs(score - threshold)
        comparison = "above" if suspicious else "below"
        decision = (
            f"The anomaly score of {score:.4f} was {distance:.4f} {comparison} "
            f"the {threshold:.4f} decision threshold"
        )
    else:
        decision = (
            "The request crossed the model's decision threshold"
            if suspicious
            else "The request remained below the model's decision threshold"
        )

    if not reasons:
        return [], f"{decision}. Its measured features are within the model's normal range."
    return reasons, f"{decision}. " + ". ".join(reasons) + "."
