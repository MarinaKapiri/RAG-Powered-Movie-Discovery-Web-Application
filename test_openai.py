from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6",
    input="Πρότεινέ μου 3 science fiction ταινίες."
)

print(response.output_text)