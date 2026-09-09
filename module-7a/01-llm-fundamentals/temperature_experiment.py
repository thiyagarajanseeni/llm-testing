from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

prompt = "A patient asks: what is the standard adult dosage for ibuprofen?"
messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content="You are a medical information assistant."),
            ChatCompletionUserMessageParam(role="user", content=prompt),]
results = {}

for temp in [0.0, 0.5, 1.0]:
    results[temp] = []
    for run in range(5):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temp,
            messages=messages,
        )
        results[temp].append(response.choices[0].message.content)

# Print results for comparison
for temp, responses in results.items():
    print(f"\n=== Temperature: {temp} ===")
    for i, r in enumerate(responses):
        print(f"Run {i+1}: {r[:100]}...")