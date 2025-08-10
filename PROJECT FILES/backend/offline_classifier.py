def offline_classify(transcript):
    lower = transcript.lower()
    keywords = [w for w in ["transfer", "bank", "account", "otp", "code", "verify", "password", "ssn"] if w in lower]
    if len(keywords) >= 2:
        return {"label": "Scam", "confidence": 0.85, "rationale": "Multiple financial keywords detected", "keywords": keywords}
    elif len(keywords) == 1:
        return {"label": "Suspicious", "confidence": 0.6, "rationale": "Single suspicious keyword", "keywords": keywords}
    else:
        return {"label": "Safe", "confidence": 0.2, "rationale": "No suspicious keywords", "keywords": []}
