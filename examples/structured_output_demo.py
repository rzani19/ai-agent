from ollama import chat


response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": "Return the result of 125 * 8.",
        }
    ],
    format={
        "type": "object",
        "properties": {
            "operation": {
                "type": "string"
            },
            "answer": {
                "type": "integer"
            }
        },
        "required": ["operation", "answer"],
    },
)

print(response.message.content)
