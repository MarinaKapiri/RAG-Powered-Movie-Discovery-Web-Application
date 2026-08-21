# IMDb Clone / Movie Recommendation RAG
## Setup on a new Windows laptop

This project contains:

- FastAPI backend
- React / Vite frontend
- PostgreSQL + pgvector
- IMDb movie/person data
- Hosted embeddings
- Local embeddings
- Semantic Search
- RAG
- OpenRouter hosted AI
- Ollama local AI

The final PostgreSQL database backup is stored in GitHub using Git LFS:

`imdb_clone_final.dump`

---

# 1. Install required software

Install:

- Git
- Git LFS
- Docker Desktop
- Python 3.13
- Node.js
- VS Code
- Ollama

Make sure Docker Desktop is running before starting the project.

---

# 2. Clone the repository

Open PowerShell:

```powershell
git lfs install
```

Then:

```powershell
git clone https://github.com/MarinaKapiri/movie-recomendation-RAG.git
```

Enter the project:

```powershell
cd movie-recomendation-RAG
```

Check that the database backup was downloaded:

```powershell
Get-Item .\imdb_clone_final.dump
```

It should be approximately **130 MB**.

You can also verify Git LFS:

```powershell
git lfs ls-files
```

It should show:

```text
imdb_clone_final.dump
```

---

# 3. Create Python environment

From the project root:

```powershell
py -m venv .venv
```

Upgrade pip:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Install backend dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

# 4. Install frontend dependencies

```powershell
cd frontend
npm ci
cd ..
```

---

# 5. OpenRouter API key

The API key is NOT stored in GitHub.

Set it in Windows:

```powershell
setx OPENROUTER_API_KEY "YOUR_OPENROUTER_KEY"
```

Do NOT save the real API key inside the repository.

After using `setx`, close and reopen VS Code / PowerShell.

If the old OpenRouter key is unavailable, create a new key from the OpenRouter account.

---

# 6. Install local AI models

Make sure Ollama is installed.

Run:

```powershell
ollama pull qwen3.5:4b
```

Then:

```powershell
ollama pull nomic-embed-text
```

Models used by the project:

- LLM: `qwen3.5:4b`
- Embeddings: `nomic-embed-text`

There is no need to transfer the Ollama model files from the old laptop.

---

# 7. Start PostgreSQL

Make sure Docker Desktop says that the engine is running.

From the project root:

```powershell
docker compose up -d
```

Check:

```powershell
docker compose ps
```

The PostgreSQL container should be running as:

```text
imdb-postgres
```

---

# 8. Restore the full database

Copy the backup into the PostgreSQL container:

```powershell
docker cp .\imdb_clone_final.dump imdb-postgres:/tmp/imdb_clone_final.dump
```

Restore it:

```powershell
docker exec imdb-postgres pg_restore -U imdb_user -d imdb_clone --clean --if-exists /tmp/imdb_clone_final.dump
```

The database backup contains:

- 9,999 movies
- people
- movie/person relationships
- hosted 2048-dimensional embeddings
- local 768-dimensional embeddings
- pgvector database structure

---

# 9. Verify database restoration

Run:

```powershell
docker exec imdb-postgres psql -U imdb_user -d imdb_clone -c "SELECT COUNT(*) AS total, COUNT(embedding) AS hosted, COUNT(embedding_local) AS local FROM movies;"
```

Expected result:

```text
 total | hosted | local
-------+--------+-------
  9999 |   9999 |  9999
```

---

# 10. AI mode

In:

```text
backend/main.py
```

there is:

```python
AI_MODE = "local"
```

Use:

```python
AI_MODE = "local"
```

for Ollama.

Use:

```python
AI_MODE = "hosted"
```

for OpenRouter.

Only this line needs to change to switch between the two modes.

---

# 11. Start backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

Leave this terminal running.

---

# 12. Start frontend

Open a second terminal:

```powershell
cd frontend
npm run dev
```

Frontend:

```text
http://localhost:5173/
```

---

# Normal startup after everything has been installed

### 1. Start Docker Desktop

Wait until Docker Engine is running.

### 2. Start database

```powershell
docker compose up -d
```

### 3. Start backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

### 4. Start frontend in another terminal

```powershell
cd frontend
npm run dev
```

### 5. Open

```text
http://localhost:5173/
```

---

# Normal shutdown

Frontend terminal:

```text
Ctrl+C
```

Backend terminal:

```text
Ctrl+C
```

Then:

```powershell
docker compose stop
```

---

# Important files

Backend:

```text
backend/main.py
```

Frontend:

```text
frontend/src/App.jsx
```

Docker:

```text
docker-compose.yml
```

Python dependencies:

```text
requirements.txt
```

Hosted embedding generator:

```text
generate_embeddings.py
```

Local embedding generator:

```text
generate_local_embeddings.py
```

Final database backup:

```text
imdb_clone_final.dump
```

---

# Current architecture

## Hosted mode

LLM:

```text
google/gemma-4-26b-a4b-it:free
```

Embedding model:

```text
nvidia/llama-nemotron-embed-vl-1b-v2:free
```

Embedding column:

```text
embedding
```

Dimensions:

```text
2048
```

Hosted free models may sometimes return rate-limit or availability errors.

## Local mode

LLM:

```text
qwen3.5:4b
```

Embedding model:

```text
nomic-embed-text
```

Embedding column:

```text
embedding_local
```

Dimensions:

```text
768
```

---

# Current project status

Completed:

- Phase 1: PostgreSQL + FastAPI + React + IMDb data
- Phase 2: Natural-language AI movie search
- Phase 3: pgvector semantic search
- Phase 4: RAG retrieval + reranking + answer generation
- Phase 5: Local AI + hosted/local switching

Next major phase:

- Phase 6: Deployment / packaging