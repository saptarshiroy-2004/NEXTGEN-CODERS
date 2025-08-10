import openai
openai.api_key = "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"

try:
    resp = openai.models.list()
    print("✅ API key works! Models:", [m.id for m in resp.data[:5]])
except Exception as e:
    print("❌ API key error:", e)
