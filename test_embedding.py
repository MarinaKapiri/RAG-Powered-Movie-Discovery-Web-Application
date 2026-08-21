import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

response = client.embeddings.create(
    model="nvidia/llama-nemotron-embed-vl-1b-v2:free",
    input="The Matrix, 1999, Action, Sci-Fi",
    encoding_format="float"
)

embedding = response.data[0].embedding

print("Μήκος embedding:", len(embedding))
print("Πρώτοι 5 αριθμοί:", embedding[:5])