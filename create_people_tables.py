import psycopg

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
    CREATE TABLE IF NOT EXISTS people (
        id SERIAL PRIMARY KEY,
        imdb_id VARCHAR(20) UNIQUE NOT NULL,
        name TEXT NOT NULL
    );
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS movie_people (
        id SERIAL PRIMARY KEY,
        movie_id INTEGER NOT NULL
            REFERENCES movies(id)
            ON DELETE CASCADE,
        person_id INTEGER NOT NULL
            REFERENCES people(id)
            ON DELETE CASCADE,
        role TEXT NOT NULL,
        character_name TEXT,
        UNIQUE (movie_id, person_id, role)
    );
    """
)

connection.commit()

cursor.close()
connection.close()

print("Οι πίνακες people και movie_people δημιουργήθηκαν επιτυχώς!")