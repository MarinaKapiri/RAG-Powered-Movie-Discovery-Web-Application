import csv
import gzip
import json
from pathlib import Path

import psycopg


PRINCIPALS_FILE = Path("data/title.principals.tsv.gz")
NAMES_FILE = Path("data/name.basics.tsv.gz")
CREW_FILE = Path("data/title.crew.tsv.gz")

DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "imdb_clone",
    "user": "imdb_user",
    "password": "imdb_password",
}


def read_characters(value):
    """Μετατρέπει το πεδίο χαρακτήρων του IMDb σε απλό κείμενο."""

    if value == r"\N":
        return None

    try:
        characters = json.loads(value)

        if isinstance(characters, list):
            return ", ".join(characters)
    except json.JSONDecodeError:
        pass

    return value


print("Φορτώνω τις 10.000 ταινίες από τη βάση...")

with psycopg.connect(**DATABASE_CONFIG) as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, imdb_id
            FROM movies;
            """
        )

        movie_ids = {
            imdb_id: movie_id
            for movie_id, imdb_id in cursor.fetchall()
        }

print(f"Βρέθηκαν {len(movie_ids)} ταινίες.")


# Το key είναι: movie_id, IMDb person ID, role
# Το value είναι το όνομα του χαρακτήρα.
relations = {}
needed_people = set()


print("Διαβάζω τους ηθοποιούς από το title.principals...")

with gzip.open(
    PRINCIPALS_FILE,
    mode="rt",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file, delimiter="\t")

    for line_number, row in enumerate(reader, start=1):
        imdb_movie_id = row["tconst"]

        if imdb_movie_id not in movie_ids:
            continue

        if row["category"] not in {"actor", "actress"}:
            continue

        movie_id = movie_ids[imdb_movie_id]
        person_imdb_id = row["nconst"]
        character_name = read_characters(row["characters"])

        relations[
            (movie_id, person_imdb_id, "actor")
        ] = character_name

        needed_people.add(person_imdb_id)

        if line_number % 5_000_000 == 0:
            print(f"Έχουν διαβαστεί {line_number:,} γραμμές...")


print("Διαβάζω τους σκηνοθέτες από το title.crew...")

with gzip.open(
    CREW_FILE,
    mode="rt",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file, delimiter="\t")

    for row in reader:
        imdb_movie_id = row["tconst"]

        if imdb_movie_id not in movie_ids:
            continue

        if row["directors"] == r"\N":
            continue

        movie_id = movie_ids[imdb_movie_id]

        for person_imdb_id in row["directors"].split(","):
            relations[
                (movie_id, person_imdb_id, "director")
            ] = None

            needed_people.add(person_imdb_id)


print(
    f"Χρειάζομαι τα ονόματα "
    f"{len(needed_people):,} ανθρώπων."
)

print("Διαβάζω τα ονόματα από το name.basics...")

people = {}

with gzip.open(
    NAMES_FILE,
    mode="rt",
    encoding="utf-8",
    newline="",
) as file:
    reader = csv.DictReader(file, delimiter="\t")

    for line_number, row in enumerate(reader, start=1):
        person_imdb_id = row["nconst"]

        if person_imdb_id in needed_people:
            people[person_imdb_id] = row["primaryName"]

        if len(people) == len(needed_people):
            break

        if line_number % 5_000_000 == 0:
            print(f"Έχουν διαβαστεί {line_number:,} ονόματα...")


print(f"Βρέθηκαν {len(people):,} ονόματα.")
print("Αποθήκευση στην PostgreSQL...")

with psycopg.connect(**DATABASE_CONFIG) as connection:
    with connection.cursor() as cursor:
        # Αδειάζουμε μόνο τους πίνακες ανθρώπων και σχέσεων,
        # ώστε να μην υπάρξουν διπλές εγγραφές.
        cursor.execute(
            """
            TRUNCATE TABLE movie_people, people
            RESTART IDENTITY;
            """
        )

        cursor.executemany(
            """
            INSERT INTO people (
                imdb_id,
                name
            )
            VALUES (%s, %s);
            """,
            [
                (person_imdb_id, name)
                for person_imdb_id, name in people.items()
            ],
        )

        cursor.execute(
            """
            SELECT id, imdb_id
            FROM people;
            """
        )

        person_ids = {
            imdb_id: person_id
            for person_id, imdb_id in cursor.fetchall()
        }

        movie_people_rows = []

        for (
            movie_id,
            person_imdb_id,
            role,
        ), character_name in relations.items():
            person_id = person_ids.get(person_imdb_id)

            if person_id is None:
                continue

            movie_people_rows.append(
                (
                    movie_id,
                    person_id,
                    role,
                    character_name,
                )
            )

        cursor.executemany(
            """
            INSERT INTO movie_people (
                movie_id,
                person_id,
                role,
                character_name
            )
            VALUES (%s, %s, %s, %s);
            """,
            movie_people_rows,
        )

    connection.commit()


print(
    f"Αποθηκεύτηκαν {len(people):,} άνθρωποι "
    f"και {len(movie_people_rows):,} συνδέσεις με ταινίες."
)
print("Η εισαγωγή ολοκληρώθηκε επιτυχώς!")