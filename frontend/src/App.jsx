import { useEffect, useRef, useState } from "react";
import "./App.css";

function App() {
  const [movies, setMovies] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedMovie, setSelectedMovie] = useState(null);

  const movieDetailsRef = useRef(null);

  function loadMovies(url) {
    setLoading(true);
    setError("");

    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Δεν ήταν δυνατή η φόρτωση των ταινιών.");
        }

        return response.json();
      })
      .then((data) => {
        setMovies(data);
        setLoading(false);
      })
      .catch((error) => {
        setError(error.message);
        setLoading(false);
      });
  }

  function loadMovieDetails(movieId) {
  fetch(`http://127.0.0.1:8000/movies/${movieId}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Δεν ήταν δυνατή η φόρτωση της ταινίας.");
      }

      return response.json();
    })
    .then((data) => {
      setSelectedMovie(data);
    })
    .catch((error) => {
      setError(error.message);
    });
  }

  useEffect(() => {
    loadMovies("http://127.0.0.1:8000/movies");

    fetch("http://127.0.0.1:8000/recommendations")
  .then((response) => response.json())
  .then((data) => setRecommendations(data));
  }, []);

  useEffect(() => {
    if (selectedMovie && movieDetailsRef.current) {
      movieDetailsRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  }, [selectedMovie]);

  function handleSearch(event) {
    event.preventDefault();
    setSelectedMovie(null);

    if (query.trim() === "") {
      loadMovies("http://127.0.0.1:8000/movies");
      return;
    }

    loadMovies(
      `http://127.0.0.1:8000/movies/search?q=${encodeURIComponent(query)}`
    );
  }

  return (
    <main>
      <h1>IMDb Clone</h1>

      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Αναζήτησε ταινία..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />

        <button type="submit">Αναζήτηση</button>
      </form>

      {selectedMovie && (
        <section 
          className="movie-details"
          ref={movieDetailsRef}
        >
          
          <h2>{selectedMovie.title}</h2>

          <p>Έτος: {selectedMovie.year}</p>
          <p>Διάρκεια: {selectedMovie.runtime_minutes} λεπτά</p>
          <p>Είδη: {selectedMovie.genres}</p>
          <p>Rating: {selectedMovie.rating}</p>
          <p>Ψήφοι: {selectedMovie.votes}</p>
          <p>
            Σκηνοθέτες: {selectedMovie.directors?.join(", ")}
          </p>

          <h3>Ηθοποιοί</h3>

          <ul>
            {selectedMovie.actors?.map((actor) => (
              <li key={`${actor.name}-${actor.character_name}`}>
                {actor.name}
                {actor.character_name && ` ως ${actor.character_name}`}
              </li>
            ))}
          </ul>
          
          <button
            type="button"
            onClick={() => setSelectedMovie(null)}
          >
            Κλείσιμο
          </button>
        </section>
      )}

      <h2>Ταινίες</h2>

      {loading && <p>Φόρτωση ταινιών...</p>}

      {error && <p>{error}</p>}

      {!loading && !error && movies.length === 0 && (
        <p>Δεν βρέθηκαν ταινίες.</p>
      )}

      {!loading &&
        !error &&
        movies.map((movie) => (
          <div key={movie.id} className="movie-card">
            <h3
              onClick={() => loadMovieDetails(movie.id)}
              style={{ 
                cursor: "pointer",
                display: "inline-block",
              }}
            >
              {movie.title}
            </h3>

            <p>
              {movie.year} | {movie.genres} | Rating: {movie.rating}
            </p>
          </div>
        ))}

      <h2>Προτάσεις για εσένα</h2>

      {recommendations.map((movie) => (
        <div key={movie.id} className="movie-card">
          <h3
            onClick={() => loadMovieDetails(movie.id)}
            style={{
              cursor: "pointer",
              display: "inline-block",
            }}
          >
            {movie.title}
          </h3>

         <p>
            {movie.year} | {movie.genres} | Rating: {movie.rating}
          </p>
        </div>
      ))}

    </main>
  );
}

export default App;