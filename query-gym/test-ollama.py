from querygym.core.llm import OpenAICompatibleClient

client = OpenAICompatibleClient(
    model="qwen3.5:9b",
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama",
)

response = client.chat(
    [
        {
            "role": "system",
            "content": "You are a helpful assistant. Answer with text only, no markdown.",
        },
        {
            "role": "user",
            "content": "What is the time complexity of Bubble Sort?",
        },
    ],
    temperature=0,
    seed=42,
    max_tokens=256,
    reasoning_effort="none",
)

print(repr(response))