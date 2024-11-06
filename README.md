# NorecipesAPI

![Python](https://img.shields.io/badge/python-3.12-blue) ![Django](https://img.shields.io/badge/django-4.2-darkgreen) ![DRF](https://img.shields.io/badge/DRF-3.15-red)

A REST API backend for a food recipe site, built in Django Rest Framework. Supports user accounts with email verification, recipe publishing with a moderation queue, an ingredient inventory system, and a search layer that can filter recipes by how many servings the user can actually cook from their current inventory.


## Highlights

- **Custom JWT authentication** with `details_iteration` token invalidation on credential change (no token blacklist table needed).
- **Recipe moderation workflow** — unsubmitted → submitted → accepted/denied with deny reasons; auto-accept for moderator-authored recipes.
- **Inventory-aware recipe search** — given a user's pantry, find recipes they can cook *enough portions of*, computed in a single annotated query (`Subquery` + `ExpressionWrapper` + `Min` aggregation).
- **Generic AND/OR substring search** across multiple fields with light morphological normalization (strip `'s`, plural `s`).
- **Time-windowed ordering** — sort by "popularity in the last N days" via dynamic queryset annotation rewrites.
- **Role-based permission system** (Anon / User / Verified / Moderator / Admin) with role-gated query parameters (e.g. `submit_status` filter accepts different values per role).
- **Rate-limited content creation** — per-user, per-resource, per-time-window limits enforced at the serializer layer.
- **222 tests**, runs against in-memory SQLite locally, Postgres in Docker.


## Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| Framework | Django 4.2 (LTS) + Django REST Framework 3.15 |
| Database | Postgres 16 in Docker; SQLite fallback for local dev/tests |
| Auth | Custom JWT (PyJWT) over Django's `PBKDF2PasswordHasher` |
| Image handling | Pillow |
| File storage | Local filesystem; pluggable S3-compatible backend via `django-storages` |
| WSGI server | Gunicorn |
| Container | Docker + Docker Compose |


## Running it

```bash
git clone https://github.com/rezvoj/NorecipesAPI.git
cd NorecipesAPI
cp .env.example .env  # edit secrets before exposing publicly
docker compose up --build
```

API is available at `http://localhost:8000/`. Media files served from `/media/` when using local storage.

### Local dev without Docker

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Falls back to SQLite when `DATABASE_URL` is unset.

### Tests

```bash
python manage.py test
```


## Configuration

All runtime configuration is read from environment variables — see [`.env.example`](.env.example) for the full list. Highlights:

- `DATABASE_URL` — Postgres connection string; absent = local SQLite.
- `APP_USE_S3` — toggle S3-compatible storage; pair with `AWS_*` vars (works with AWS, MinIO, etc.).
- `APP_LOG_HANDLER` — dotted path to any `logging.Handler` subclass, with kwargs in `APP_LOG_HANDLER_OPTIONS` (JSON). Default is stdout; production can point at syslog, HTTP, Sentry, etc., without code changes.
- `APP_EMAIL_BACKEND` — `console` (dev) or `smtp` (prod).


## Architecture

```
NorecipesAPI/        # Django project (settings, root URLs)
NorecipesAPIapp/
├── models/          # User, Recipe, Category, Ingredient, Rating, etc.
├── serializers/     # DRF serializers + filter param schemas
├── views/           # APIView classes
├── utils/
│   ├── security.py     # JWT + password hashing + auth backend
│   ├── permission.py   # Role helpers (user / verified / admin / mod)
│   ├── validation.py   # Photo verification, ordering whitelist, rate limiting
│   ├── filtering.py    # Reusable search, order_by, paginate helpers
│   ├── verification.py # Email + password reset code flows
│   └── exception.py    # Custom exception → HTTP response mapping
└── tests/           # 222 tests covering auth, CRUD, filtration, moderation
```


## Roles

| Role | Means |
| --- | --- |
| **Anon** | No JWT or invalid JWT. |
| **User** | Valid JWT in `Authorization: Bearer <token>`. |
| **Verified** | User who completed email verification. Required to publish content. |
| **Moderator** | User flagged as moderator by an admin. Can accept/deny recipes, ban users. |
| **Admin** | Holds the configured `ADMINCODE` in request headers. Out-of-band trust, not a user account. |


## API

Full endpoint reference: [ENDPOINTS.md](ENDPOINTS.md).

### Examples

Fetch a recipe (Authorization optional but enriches the response with `favoured`, `cookable_portions`, etc.):
```bash
curl -X GET http://localhost:8000/recipe/detail/23 \
    -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Rate a recipe:
```bash
curl -X POST http://localhost:8000/rating/3 \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -F "photo=@path/to/file.jpg" \
    -F "stars=5" \
    -F "content=I really liked this."
```

### Date/time convention

The API uses **naive UTC** datetimes throughout — both inputs and outputs are ISO 8601 without timezone suffix (e.g. `2023-07-11T14:30:00`). Inputs with `Z` or numeric offsets are rejected. Clients are expected to normalize to UTC before sending.


## Error responses

| Status | Cause | Body |
| --- | --- | --- |
| 400 | Validation error | `{"detail": {"field_name": ["message", ...], ...}}` |
| 400 | Content rate limit exceeded | `{"detail": {"limit": 10, "hours": 1}}` |
| 401 | Missing/insufficient permissions | `{}` |
| 403 | User is banned | `{"detail": "You have been banned."}` |
| 404 | Resource not found or not accessible to caller | `{}` |
