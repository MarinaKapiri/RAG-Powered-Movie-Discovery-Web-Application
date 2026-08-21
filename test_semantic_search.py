import os

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row


MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "imdb_clone",
    "user": "imdb_user",
    "password": "imdb_password",
}


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


query = "dark philosophical science fiction"


print("Δημιουργώ embedding για το query...")

response = client.embeddings.create(
    model=MODEL,
    input=query,
    encoding_format="float",
)

query_embedding = response.data[0].embedding

vector_string = (
    "["
    + ",".join(str(value) for value in query_embedding)
    + "]"
)


print("Ψάχνω τις πιο κοντινές ταινίες...")


with psycopg.connect(
    **DATABASE_CONFIG,
    row_factory=dict_row,
) as connection:

    with connection.cursor() as cursor:

        cursor.execute(
            """
            SELECT
                id,
                title,
                year,
                genres,
                rating,
                embedding <=> %s::vector AS distance
            FROM movies
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
            """,
            (
                vector_string,
                vector_string,
            ),
        )

        movies = cursor.fetchall()


print("\nΑποτελέσματα:\n")

for movie in movies:
    print(
        f"{movie['title']} ({movie['year']}) "
        f"| {movie['genres']} "
        f"| distance: {movie['distance']:.4f}"
    )