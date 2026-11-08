# Equipment Borrowing and Return System

**Group 3**

Group Members:
1. Domingo, Royvil
2. Galvez, Rainiel
3. Naga, Chelzy Mariz
4. Nicolas, Clarence Dave
5. Perez, Mark Paler
6. Timoteo, Jimuel Josh

A Flask web app for tracking equipment availability, borrower requests, and admin-approved borrowing transactions.

**Stack:** Python • Flask • HTML/Bootstrap • SQL • SQLite (SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF)

## Roles

- **Admin**: manages equipment, views registered borrowers, reviews and approves/rejects borrowing requests, processes returns, and views full borrowing history, overdue items, and SQL reports.
- **Borrower**: registers an account, browses available equipment, submits borrowing requests, and tracks the status of their own requests.

There is no public registration for admin accounts. The first admin is created with a CLI command (step 6 below).

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/Royvil-Domingo/flask-project.git
   cd flask-project
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # macOS/Linux
   ```
   Open `.env` and replace `SECRET_KEY` with your own generated value:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Leave `DATABASE_URL` commented out. The app then uses a local SQLite file at `instance/database.db`.

5. **Initialize the database**
   ```bash
   set FLASK_APP=run.py        # Windows
   export FLASK_APP=run.py     # macOS/Linux
   flask db stamp head
   ```
   The app creates every table from the models the first time any `flask` command loads it, so this fresh database already has the current schema. `flask db stamp head` then records that it is up to date with the migration history. **Do not run `flask db upgrade` on a brand-new database**: the tables already exist and the migration would try to add columns that are already there.

6. **Create the first admin account**
   ```bash
   flask seed-admin
   ```
   Prompts for an email, name, and password.

7. **Run the app**
   ```bash
   python run.py
   ```
   Visit `http://127.0.0.1:5000`. Log in with the admin account from step 6, or use **Sign Up** to register a borrower account.

**Updating an older database** that was created before a schema change: pull the latest code, then run `flask db upgrade`.

## Pages

| Page | Who | Route |
|---|---|---|
| Login | Everyone | `/login` |
| Sign Up (borrower registration) | Public | `/register` |
| Dashboard (admin or borrower view) | Logged in | `/dashboard` |
| Equipment catalog and search | Logged in | `/equipment/` |
| Equipment management (add/edit/delete) | Admin | `/equipment/add`, `/equipment/edit/<id>` |
| Borrowers directory (add/edit/delete) | Admin | `/borrowers/` |
| Request Equipment | Borrower | `/borrowings/request` |
| My Borrowings | Borrower | `/borrowings/mine` |
| Pending Requests (approve/reject) | Admin | `/borrowings/requests` |
| Borrowing History (search, filters, overdue, returns) | Admin | `/borrowings/` |
| SQL Reports (overdue, availability, status summary) | Admin | `/reports` |

## Borrowing workflow

A request starts as `pending` and does not affect available stock. An admin approves it (deducting stock and recording the issue date) or rejects it (stock unchanged, optional reason). Once borrowed, an admin processes the return, which restores stock. Status values: `pending`, `borrowed`, `rejected`, `returned`. "Overdue" is a calculated display state on top of `borrowed`, not a separate status.

A request can never exceed available stock. This is checked when the request is submitted and checked again, atomically, at approval.

## Database

Four related tables: `users`, `borrowers`, `equipment`, `borrowings`, with primary keys, foreign keys, unique constraints, and CHECK constraints (quantities can't go negative, available can't exceed total). The full schema is in [`schema.sql`](schema.sql).

How the layers fit together: an HTML form posts to a Flask route, the route validates input in Python, and the Python code reads or writes SQLite through parameterized SQL (SQLAlchemy ORM queries and the hand-written `text()` queries in `app/utils/sql_reports.py`, which the Reports page displays alongside their results).

Deleting equipment or a borrower is blocked once they have borrowing history, so the audit trail stays intact.

## Security

- Passwords are stored as salted hashes.
- Roles are enforced on the server with decorators. Borrowers can only see their own records, and the role is never read from a submitted form.
- Every POST form carries a CSRF token (Flask-WTF).
- Transactions (approve, reject, return) use conditional updates and roll back on any error, so stock can't be double-deducted or double-restored.

## Deployment (optional)

The app can be deployed on Vercel at `https://flask-project-three-mauve.vercel.app/`, backed by a Postgres database on [Neon](https://neon.tech), because serverless functions have a read-only filesystem and can't use SQLite.

**One-time production setup:**
1. Create a Neon Postgres database and copy its connection string.
2. From a local machine, temporarily point `.env`'s `DATABASE_URL` at it (use the `postgresql+psycopg2://` scheme, required since SQLAlchemy 2.1 defaults to a different driver) and run:
   ```bash
   flask db stamp head
   flask seed-admin
   ```
   The first command creates the tables from the models and records the migration state. Then switch `.env` back so local development keeps using SQLite.
3. In Vercel's project settings → Environment Variables, set:
   - `SECRET_KEY`: a freshly generated value, separate from the local one. The app refuses to start in production without it.
   - `DATABASE_URL`: the Neon connection string with `postgresql+psycopg2://` as the scheme.

**Ongoing deploys:** pushing to `main` redeploys automatically. Vercel does not run migrations. After a schema change, run `flask db upgrade` against the Neon database first, with the same temporary `.env` switch.