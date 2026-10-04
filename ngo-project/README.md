# Hope NGO Management – Dashboard & Beneficiaries

React + Vite frontend  →  REST API  →  FastAPI  →  SQLAlchemy  →  SQLite

## Run (two terminals)

**1. Backend** (terminal 1)
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate      macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (terminal 2, project root)
```bash
npm install
npm run dev
```
Open http://localhost:5173. The API docs are at http://localhost:8000/docs.

The frontend talks to `http://localhost:8000` by default. To use another address create a `.env` file containing
`VITE_API_URL=http://your-host:port`.

See `backend/README.md` for the API reference and Postman instructions.
