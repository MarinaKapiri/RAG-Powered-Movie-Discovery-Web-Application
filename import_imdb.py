import csv
import gzip
from pathlib import Path

import psycopg


BASICS_FILE = Path("data/title.basics.tsv.gz")
RATINGS_FILE = Path("data/title.ratings.tsv.gz")

MOVIE_LIMIT = 10_000
MIN_VOTES = 1_000


def to_integer(value):
    if value == r"\N":
        return None

    return int(value)


print("Διαβάζω τα ratings...")

ratings = {}

with gzip.open(
    RATINGS_FILE,
    mode="rt",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file, delimiter="\t")

    for row in reader:
        votes = int(row["numVotes"])

        if votes >= MIN_VOTES:
            ratings[row["tconst"]] = (
                float(row["averageRating"]),
                votes,
            )


print("Διαβάζω τις ταινίες...")

movies = []

with gzip.open(
    BASICS_FILE,
    mode="rt",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file, delimiter="\t")

    for row in reader:
        if row["titleType"] != "movie":
            continue

        if row["isAdult"] != "0":
            continue

        imdb_id = row["tconst"]

        if imdb_id not in ratings:
            continue

        rating, votes = ratings[imdb_id]

        genres = None if row["genres"] == r"\N" else row["genres"]

        original_title = (
            None
            if row["originalTitle"] == r"\N"
            else row["originalTitle"]
        )

        movies.append(
            (
                imdb_id,
                row["primaryTitle"],
                original_title,
                to_integer(row["startYear"]),
                to_integer(row["runtimeMinutes"]),
                genres,
                rating,
                votes,
            )
        )


movies.sort(key=lambda movie: movie[7], reverse=True)
movies = movies[:MOVIE_LIMIT]

print(f"Επιλέχθηκαν {len(movies)} ταινίες.")
print("Αποθήκευση στην PostgreSQL...")


connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="imdb_clone",
    user="imdb_user",
    password="imdb_password",
)

cursor = connection.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS movies (
        id SERIAL PRIMARY KEY,
        imdb_id VARCHAR(20) UNIQUE NOT NULL,
        title TEXT NOT NULL,
        original_title TEXT,
        year INTEGER,
        runtime_minutes INTEGER,
        genres TEXT,
        rating DECIMAL(3, 1),
        votes INTEGER
    );
    """
)

cursor.execute("TRUNCATE TABLE movies RESTART IDENTITY;")

cursor.executemany(
    """
    INSERT INTO movies (
        imdb_id,
        title,
        original_title,
        year,
        runtime_minutes,
        genres,
        rating,
        votes
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """,
    movies,
)

connection.commit()

cursor.close()
connection.close()

print("Οι 10.000 ταινίες αποθηκεύτηκαν επιτυχώς!")