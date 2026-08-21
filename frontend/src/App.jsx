import { useEffect, useRef, useState } from "react";
import "./App.css";

function App() {
  const [movies, setMovies] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [aiQuery, setAiQuery] = useState("");
  const [aiMovies, setAiMovies] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);
  const movieDetailsRef = useRef(null);
  const [semanticQuery, setSemanticQuery] = useState("");
  const [semanticMovies, setSemanticMovies] = useState([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [ragQuery, setRagQuery] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [ragLoading, setRagLoading] = useState(false);

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

  async function handleAiSearch(event) {
    event.preventDefault();

    if (aiQuery.trim() === "") {
      return;
    }

    setAiLoading(true);
    setAiMovies([]);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/ai-search?q=${encodeURIComponent(aiQuery)}`
      );

      if (!response.ok) {
        throw new Error("Αποτυχία AI αναζήτησης.");
      }

      const data = await response.json();

      setAiMovies(data.movies);
    } catch (error) {
      setError(error.message);
    } finally {
      setAiLoading(false);
    }
  }

  async function handleSemanticSearch(event) {
    event.preventDefault();

    if (semanticQuery.trim() === "") {
      return;
    }

    setSemanticLoading(true);
    setSemanticMovies([]);

    try {
     const response = await fetch(
       `http://127.0.0.1:8000/semantic-search?q=${encodeURIComponent(semanticQuery)}`
      );

      if (!response.ok) {
        throw new Error("Αποτυχία semantic search.");
      }

      const data = await response.json();

      setSemanticMovies(data);
    } catch (error) {
     setError(error.message);
    } finally {
      setSemanticLoading(false);
   }
  }

  async function handleRagSearch(event) {
    event.preventDefault();

    if (ragQuery.trim() === "") {
      return;
    }

    setRagLoading(true);
    setRagAnswer("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/rag-search?q=${encodeURIComponent(ragQuery)}`
      );

      if (!response.ok) {
        throw new Error("Αποτυχία RAG search.");
      }

      const data = await response.json();

      setRagAnswer(data.rag_answer);
    } catch (error) {
      setError(error.message);
    } finally {
      setRagLoading(false);
    }
  }

  return (
    <main>
      <h1>IMDb Clone</h1>

      <h2>AI Search</h2>

      <form onSubmit={handleAiSearch}>
        <input
          type="text"
          placeholder="π.χ. θέλω σκοτεινό sci-fi σαν το Matrix"
          value={aiQuery}
          onChange={(event) => setAiQuery(event.target.value)}
        />

        <button type="submit" disabled={aiLoading}>
          {aiLoading ? "Ψάχνω..." : "Ρώτα το AI"}
        </button>
      </form>

      {aiLoading && <p>Το AI ψάχνει ταινίες...</p>}

      {aiMovies.length > 0 && (
        <>
          <h2>AI Προτάσεις</h2>

          {aiMovies.map((movie) => (
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
        </>
      )}

      <h2>Semantic Search</h2>

      <form onSubmit={handleSemanticSearch}>
        <input
          type="text"
          placeholder="π.χ. dark philosophical science fiction"
          value={semanticQuery}
          onChange={(event) => setSemanticQuery(event.target.value)}
        />

        <button type="submit" disabled={semanticLoading}>
          {semanticLoading ? "Ψάχνω..." : "Semantic Search"}
        </button>
      </form>

      {semanticLoading && <p>Γίνεται semantic search...</p>}

      {semanticMovies.length > 0 && (
        <>
          <h2>Semantic αποτελέσματα</h2>

          {semanticMovies.map((movie) => (
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
        </>
      )}

      <h2>RAG Search</h2>

      <form onSubmit={handleRagSearch}>
        <input
          type="text"
          placeholder="π.χ. dark philosophical science fiction"
          value={ragQuery}
          onChange={(event) => setRagQuery(event.target.value)}
        />

        <button type="submit" disabled={ragLoading}>
          {ragLoading ? "Σκέφτομαι..." : "RAG Search"}
        </button>
      </form>

      {ragLoading && <p>Το RAG ετοιμάζει απάντηση...</p>}

      {ragAnswer && (
        <div className="movie-details">
          <h2>RAG Απάντηση</h2>
          <p style={{ whiteSpace: "pre-line" }}>{ragAnswer}</p>
        </div>
      )}

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