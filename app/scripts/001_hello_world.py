import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

message = client.messages.create(
    model=os.getenv("ANTROPIC_MODEL", ""),
    max_tokens=100,
    messages=[
        {
            "role": "user",
            "content": "Hello, how are you?",
        }
    ],
)

for block in message.content:
    if block.type == "text":
        print(block.text)
