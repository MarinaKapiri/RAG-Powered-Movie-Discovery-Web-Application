import os
import time

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row


MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
BATCH_SIZE = 50

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


def create_movie_text(movie):
    return (
        f"Title: {movie['title']}\n"
        f"Year: {movie['year']}\n"
        f"Genres: {movie['genres'] or ''}\n"
        f"Directors: {movie['directors'] or ''}\n"
        f"Actors: {movie['actors'] or ''}"
    )


total_processed = 0

while True:
    print("\nΠαίρνω το επόμενο batch από τη βάση...")

    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    m.id,
                    m.title,
                    m.year,
                    m.genres,

                    (
                        SELECT string_agg(d.name, ', ')
                        FROM (
                            SELECT p.name
                            FROM movie_people mp
                            JOIN people p
                                ON p.id = mp.person_id
                            WHERE mp.movie_id = m.id
                              AND mp.role = 'director'
                            ORDER BY mp.id
                        ) d
                    ) AS directors,

                    (
                        SELECT string_agg(a.name, ', ')
                        FROM (
                            SELECT p.name
                            FROM movie_people mp
                            JOIN people p
                                ON p.id = mp.person_id
                            WHERE mp.movie_id = m.id
                              AND mp.role = 'actor'
                            ORDER BY mp.id
                            LIMIT 5
                        ) a
                    ) AS actors

                FROM movies m
                WHERE m.embedding IS NULL
                ORDER BY m.id
                LIMIT %s;
                """,
                (BATCH_SIZE,),
            )

            movies = cursor.fetchall()

    if not movies:
        print("\nΔεν υπάρχουν άλλες ταινίες χωρίς embedding.")
        break

    print(f"Βρέθηκαν {len(movies)} ταινίες.")

    texts = [
        create_movie_text(movie)
        for movie in movies
    ]

    print("Ζητάω embeddings από το OpenRouter...")

    response = client.embeddings.create(
        model=MODEL,
        input=texts,
        encoding_format="float",
    )

    print(
        f"Παραλήφθηκαν {len(response.data)} embeddings."
    )

    with psycopg.connect(**DATABASE_CONFIG) as connection:
        with connection.cursor() as cursor:

            for movie, embedding_result in zip(
                movies,
                response.data,
            ):
                embedding = embedding_result.embedding

                vector_string = (
                    "["
                    + ",".join(
                        str(value)
                        for value in embedding
                    )
                    + "]"
                )

                cursor.execute(
                    """
                    UPDATE movies
                    SET embedding = %s::vector
                    WHERE id = %s;
                    """,
                    (
                        vector_string,
                        movie["id"],
                    ),
                )

            connection.commit()

    total_processed += len(movies)

    print(
        f"Σύνολο νέων embeddings σε αυτό το run: "
        f"{total_processed}"
    )

    # Μικρή παύση για να μην πιέζουμε συνεχώς το API.
    time.sleep(1)


print("\nΟλοκληρώθηκε η δημιουργία embeddings!")