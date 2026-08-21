import psycopg
from openai import OpenAI

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "imdb_clone",
    "user": "imdb_user",
    "password": "imdb_password",
}

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

with psycopg.connect(**DATABASE_CONFIG) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, year, genres
            FROM movies
            WHERE embedding_local IS NULL
            ORDER BY id
            LIMIT 1;
            """
        )

        movie = cursor.fetchone()

        text = (
            f"Title: {movie[1]}\n"
            f"Year: {movie[2]}\n"
            f"Genres: {movie[3]}"
        )

        response = client.embeddings.create(
            model="nomic-embed-text",
            input=text,
        )

        embedding = response.data[0].embedding

        vector_string = "[" + ",".join(str(x) for x in embedding) + "]"

        cursor.execute(
            """
            UPDATE movies
            SET embedding_local = %s::vector
            WHERE id = %s;
            """,
            (vector_string, movie[0]),
        )

        connection.commit()

        print("Movie:", movie[1])
        print("Dimensions:", len(embedding))
        print("Local embedding saved.")