# Hope NGO – Backend (FastAPI + SQLAlchemy + SQLite)

REST API for the **Beneficiaries** and **Main Dashboard** sections.

## Setup & run

```bash
cd backend
python -m venv venv
# Windows:  venv\Scripts\activate        macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

* API: http://localhost:8000  · Interactive docs (try every endpoint): http://localhost:8000/docs
* On first start the SQLite file `backend/ngo.db` is created and filled with sample beneficiaries.
* Reset the database to the sample data: `python -m app.seed`

## Endpoints

| Method | URL | Purpose |
|---|---|---|
| GET | `/api/beneficiaries` | List (optional `?search=`, `?status=`, `?skip=`, `?limit=`) |
| POST | `/api/beneficiaries` | Create → 201 |
| GET | `/api/beneficiaries/{id}` | One beneficiary (404 if missing) |
| PUT | `/api/beneficiaries/{id}` | Full update |
| DELETE | `/api/beneficiaries/{id}` | **Soft delete** – sets `status = "Inactive"` |
| GET | `/api/dashboard/statistics` | Dashboard numbers (optional `?recent_days=30`) |

Errors: `404 {"detail": "..."}` and `422 {"detail": "...", "errors": [{"field": "phone", "message": "..."}]}`.

## Testing with Postman
Import `postman_collection.json` (Postman → Import). It has the variables `baseUrl` and `beneficiaryId` and
10 ready-made requests (valid + invalid examples included).

## Folder structure
```
backend/
├── app/
│   ├── main.py          # creates the app, CORS, error format, startup (tables + sample data)
│   ├── database.py      # SQLite engine, session, get_db()
│   ├── models.py        # Beneficiary table (SQLAlchemy)
│   ├── schemas.py       # request/response shapes + validation (Pydantic)
│   ├── crud.py          # all database queries incl. dashboard calculations
│   ├── seed.py          # sample data
│   └── routers/
│       ├── beneficiaries.py
│       └── dashboard.py
├── postman_collection.json
└── requirements.txt
```
