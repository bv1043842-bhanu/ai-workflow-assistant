# CampusConnect

AI-powered campus event management application built with React, FastAPI, SQLite, and Ollama.

## Features

- Create, view, update, and delete campus events.
- Search events by title and location.
- Filter events by date.
- Paginate event results.
- Ask questions about campus events using a local AI assistant.
- Store event data persistently in SQLite.
- Validate event data through the backend.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite |
| Backend | Python, FastAPI |
| Database | SQLite |
| AI | Ollama, Llama 3.2 3B |
| Testing | pytest |

## Project Structure

```text
ai-workflow-assistant/
+-- app/
¦   +-- main.py
¦   +-- database.py
¦   +-- event_repository.py
+-- data/
+-- frontend/
¦   +-- src/
¦   +-- package.json
+-- tests/
¦   +-- test_main.py
+-- AGENTS.md
+-- requirements.txt
+-- README.md
```

## Prerequisites

- Python 3.14 or compatible version
- Node.js and npm
- Ollama installed
- Git

## Backend Setup

From the project root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install and start Ollama, then download the model:

```powershell
ollama pull llama3.2:3b
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.
Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/events` | Create an event |
| GET | `/events` | List and filter events |
| GET | `/events/{id}` | Retrieve an event |
| PUT | `/events/{id}` | Update an event |
| DELETE | `/events/{id}` | Delete an event |
| POST | `/ai/ask` | Ask the AI about campus events |

The events endpoint supports `title`, `location`, `date`, `skip`, and `limit` query parameters.

## Running Tests

From the project root with the virtual environment activated:

```powershell
python -m pytest -v
```

## Frontend Quality Checks

From the `frontend` directory:

```powershell
npm run lint
npm run build
```

## AI Assistant

The AI assistant uses the locally running Ollama service and the `llama3.2:3b` model. Its answers are grounded in the campus event data supplied by the backend.

## License

No license has been specified yet.
