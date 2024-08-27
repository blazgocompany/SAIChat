from g4f.client import Client


client = Client() 

chat_completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me about france"}],
)

print(chat_completion.choices[0].message.content or "")
