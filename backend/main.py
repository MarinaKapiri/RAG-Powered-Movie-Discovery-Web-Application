import psycopg
from psycopg import sql
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from fastapi.middleware.cors import CORSMiddleware
import os
from openai import OpenAI
import json
import re
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIST / "assets"),
    name="assets",
)

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

openai_client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
)

local_llm_client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

AI_MODE = os.getenv("AI_MODE", "local").lower()

HOSTED_LLM_MODEL = "google/gemma-4-26b-a4b-it:free"
LOCAL_LLM_MODEL = "qwen3.5:4b"

HOSTED_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
LOCAL_EMBEDDING_MODEL = "nomic-embed-text"

if AI_MODE == "local":
    active_embedding_client = local_llm_client
    active_embedding_model = LOCAL_EMBEDDING_MODEL
    active_embedding_column = "embedding_local"
else:
    active_embedding_client = openrouter_client
    active_embedding_model = HOSTED_EMBEDDING_MODEL
    active_embedding_column = "embedding"

if AI_MODE == "local":
    active_llm_client = local_llm_client
    active_llm_model = LOCAL_LLM_MODEL
else:
    active_llm_client = openai_client
    active_llm_model = "gpt-5-mini"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "imdb_clone"),
    "user": os.getenv("DB_USER", "imdb_user"),
    "password": os.getenv("DB_PASSWORD", "imdb_password"),
}


@app.get("/health")
def health():
    return {"message": "Το backend λειτουργεί!"}

@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIST / "index.html")


@app.get("/movies")
def get_movies():
    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    imdb_id,
                    title,
                    year,
                    genres,
                    rating,
                    votes
                FROM movies
                ORDER BY votes DESC
                LIMIT 10;
                """
            )

            return cursor.fetchall()
        
@app.get("/movies/search")
def search_movies(q: str):
    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    imdb_id,
                    title,
                    year,
                    genres,
                    rating,
                    votes
                FROM movies
                WHERE title ILIKE %s
                ORDER BY votes DESC
                LIMIT 20;
                """,
                (f"%{q}%",),
            )

            return cursor.fetchall()        
        
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    imdb_id,
                    title,
                    original_title,
                    year,
                    runtime_minutes,
                    genres,
                    rating,
                    votes
                FROM movies
                WHERE id = %s;
                """,
                (movie_id,),
            )

            movie = cursor.fetchone()

            if movie is None:
                raise HTTPException(
                    status_code=404,
                    detail="Η ταινία δεν βρέθηκε",
                )

            cursor.execute(
                """
                SELECT
                    people.name,
                    movie_people.character_name
                FROM movie_people
                JOIN people
                    ON people.id = movie_people.person_id
                WHERE movie_people.movie_id = %s
                  AND movie_people.role = 'actor'
                ORDER BY movie_people.id
                LIMIT 10;
                """,
                (movie_id,),
            )

            movie["actors"] = cursor.fetchall()

            cursor.execute(
                """
                SELECT people.name
                FROM movie_people
                JOIN people
                    ON people.id = movie_people.person_id
                WHERE movie_people.movie_id = %s
                  AND movie_people.role = 'director'
                ORDER BY movie_people.id;
                """,
                (movie_id,),
            )

            directors = cursor.fetchall()

            movie["directors"] = [
                director["name"]
                for director in directors
            ]

            return movie
        

@app.get("/recommendations")
def get_recommendations():
    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    imdb_id,
                    title,
                    year,
                    genres,
                    rating,
                    votes
                FROM movies
                WHERE genres ILIKE %s
                   OR genres ILIKE %s
                ORDER BY rating DESC, votes DESC
                LIMIT 10;
                """,
                ("%Sci-Fi%", "%Thriller%"),
            )

            return cursor.fetchall()

@app.get("/ai-search")
def ai_search(q: str):
    response = active_llm_client.chat.completions.create(
        model=active_llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a movie recommendation assistant. "
                    "Recommend exactly 5 movies based on the user's request. "
                    "Return ONLY valid JSON in exactly this format: "
                    '{"movies":[{"title":"Movie Title","year":2000}]}. '
                    "Each movie must contain only title and year. "
                    "Do not add markdown, explanations, numbering, or any text outside the JSON."
                ),
            },
            {
                "role": "user",
                "content": q,
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "movie_recommendations",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "movies": {
                            "type": "array",
                            "minItems": 5,
                            "maxItems": 5,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "year": {"type": "integer"}
                                },
                                "required": ["title", "year"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["movies"],
                    "additionalProperties": False
                }
            }
        },
    )
    print(response)

    answer = response.choices[0].message.content

    data = json.loads(answer)
    recommendations = data["movies"]

    movies = []

    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:

            for recommendation in recommendations:
                cursor.execute(
                    """
                    SELECT
                        id,
                        imdb_id,
                        title,
                        year,
                        genres,
                        rating,
                        votes
                    FROM movies
                    WHERE LOWER(title) = LOWER(%s)
                    AND year = %s
                    LIMIT 1;
                    """,
                    (
                    recommendation["title"],
                    recommendation["year"],
                    ),
                )

                movie = cursor.fetchone()

                if movie:
                    movies.append(movie)

    return {
        "recommended_movies": recommendations,
        "movies": movies,
    }

    titles = [
        title.strip()
        for title in answer.splitlines()
        if title.strip()
    ]

    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    imdb_id,
                    title,
                    year,
                    genres,
                    rating,
                    votes
                FROM movies
                WHERE LOWER(title) = ANY(%s);
                """,
                ([title.lower() for title in titles],),
            )

            movies = cursor.fetchall()

    return {
        "recommended_titles": titles,
        "movies": movies,
    }

@app.get("/semantic-search")
def semantic_search(q: str):

    response = active_embedding_client.embeddings.create(
        model=active_embedding_model,
        input=q,
        encoding_format="float",
    )

    embedding = response.data[0].embedding

    vector_string = (
        "["
        + ",".join(str(value) for value in embedding)
        + "]"
    )

    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                sql.SQL(
                    """
                    SELECT
                        id,
                        imdb_id,
                        title,
                        year,
                        genres,
                        rating,
                        votes,
                        {embedding_column} <=> %s::vector AS distance
                    FROM movies
                    WHERE {embedding_column} IS NOT NULL
                    ORDER BY {embedding_column} <=> %s::vector
                    LIMIT 20;
                    """
                ).format(
                    embedding_column=sql.Identifier(active_embedding_column)
                ),
                (
                    vector_string,
                    vector_string,
                ),
            )

            return cursor.fetchall()

@app.get("/rag-search")
def rag_search(q: str):

    response = active_embedding_client.embeddings.create(
        model=active_embedding_model,
        input=q,
        encoding_format="float",
    )

    embedding = response.data[0].embedding

    vector_string = (
        "["
        + ",".join(str(value) for value in embedding)
        + "]"
    )

    with psycopg.connect(
        **DATABASE_CONFIG,
        row_factory=dict_row,
    ) as connection:

        with connection.cursor() as cursor:

            cursor.execute(
                sql.SQL(
                    """
                    SELECT
                        id,
                        title,
                        year,
                        genres,
                        rating,
                        votes,
                        {embedding_column} <=> %s::vector AS distance
                    FROM movies
                    WHERE {embedding_column} IS NOT NULL
                    ORDER BY {embedding_column} <=> %s::vector
                    LIMIT 20;
                    """
                ).format(
                    embedding_column=sql.Identifier(active_embedding_column)
                ),
                (
                    vector_string,
                    vector_string,
                ),
            )   

            movies = cursor.fetchall()

    retrieval_context = "\n".join(
        f"ID: {movie['id']} | "
        f"{movie['title']} ({movie['year']}) | "
        f"Genres: {movie['genres']} | "
        f"Rating: {movie['rating']}"
        for movie in movies
    )

    if AI_MODE == "local":
        rerank_options = {
            "temperature": 0,
            "reasoning_effort": "none",
        }
    else:
        rerank_options = {}

    rerank_response = active_llm_client.chat.completions.create(
        model=active_llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a movie reranker. "
                    "Select exactly 10 movies that best match the user's request. "
                    "Use only IDs from the provided candidates. "
                    "Order them from best match to worst match."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User request:\n{q}\n\n"
                    f"Candidate movies:\n{retrieval_context}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "reranked_movies",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "ids": {
                            "type": "array",
                            "minItems": 10,
                            "maxItems": 10,
                            "items": {"type": "integer"},
                        }
                    },
                    "required": ["ids"],
                    "additionalProperties": False,
                },
            },
        },
        **rerank_options,
    )

    print("RERANK CONTENT:", repr(rerank_response.choices[0].message.content))
    print("RERANK MESSAGE:", rerank_response.choices[0].message)

    rerank_content = rerank_response.choices[0].message.content

    try:
        reranked_data = json.loads(rerank_content)
        reranked_ids = reranked_data["ids"]
    except json.JSONDecodeError:
        reranked_ids = [
            int(movie_id)
            for movie_id in re.findall(r"ID:\s*(\d+)", rerank_content)
        ]

        if len(reranked_ids) != 10:
            raise ValueError("Το reranker δεν επέστρεψε 10 έγκυρα movie IDs.")

    movies_by_id = {
        movie["id"]: movie
        for movie in movies
    }

    context_movies = [
        movies_by_id[movie_id]
        for movie_id in reranked_ids
        if movie_id in movies_by_id
    ]

    context = "\n".join(
        f"{movie['title']} ({movie['year']}) | "
        f"Genres: {movie['genres']} | "
        f"Rating: {movie['rating']}"
        for movie in context_movies
    )

    llm_response = active_llm_client.chat.completions.create(
        model=active_llm_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a movie recommendation assistant. "
                    "Use only the movies provided in the context. "
                    "Do not recommend movies that are not in the context."
                    "Return plain text only, without Markdown formatting."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User request:\n{q}\n\n"
                    f"Available movies from the database:\n{context}\n\n"
                    "Recommend the best movies for the user's request "
                    "and briefly explain why."
                ),
            },
        ],
    )

    rag_answer = llm_response.choices[0].message.content

    return {
        "query": q,
        "retrieved_movies": movies,
        "rag_context": context,
        "rag_answer": rag_answer,
        "reranked_ids": reranked_ids,
    }