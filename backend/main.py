import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "imdb_clone",
    "user": "imdb_user",
    "password": "imdb_password",
}


@app.get("/")
def home():
    return {"message": "Το backend λειτουργεί!"}


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