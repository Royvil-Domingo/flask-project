# Equipment Borrowing and Return System

A Flask web app for tracking equipment availability, borrower requests, and admin-approved borrowing transactions.

## Roles

- **Admin** — manages equipment, views registered borrowers, reviews and approves/rejects borrowing requests, processes returns, and views full borrowing history including overdue items.
- **Borrower** — registers an account, browses available equipment, submits borrowing requests, and tracks the status of their own requests.

There is no public self-registration for admin accounts — the first admin is created via a CLI command (step 6 below).

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/Royvil-Domingo/flask-project.git
   cd <repo-name>
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
   Leave `DATABASE_URL` unset (or commented out) — the app defaults to a local SQLite file under `instance/`, which is what the migrations below expect.

5. **Apply the database schema**
   ```bash
   set FLASK_APP=run.py        # Windows
   export FLASK_APP=run.py     # macOS/Linux
   flask db upgrade
   ```
   This creates `instance/database.db` with the full current schema by replaying the project's migration history — don't rely on the app creating tables on its own for a fresh clone, since that would leave the database out of sync with future migrations.

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

## Pages

| Page | Who | Route |
|---|---|---|
| Login | Everyone | `/login` |
| Sign Up (borrower registration) | Public | `/sign-up` |
| Dashboard (admin or borrower view) | Everyone | `/dashboard` |
| Equipment catalog | Everyone | `/equipment/` |
| Equipment management (add/edit/delete) | Admin | `/equipment/add`, `/equipment/edit/<id>` |
| Borrowers directory | Admin | `/borrowers/` |
| Request Equipment | Borrower | `/borrowings/request` |
| My Borrowings | Borrower | `/borrowings/mine` |
| Pending Requests (approve/reject) | Admin | `/borrowings/requests` |
| Borrowing History (search/filter, overdue) | Admin | `/borrowings/` |

## Borrowing workflow

A request starts as `pending` and does not affect available stock. An admin approves it (deducting stock and recording the issue date) or rejects it (stock unchanged). Once borrowed, an admin processes the return, which restores stock. Status values: `pending`, `borrowed`, `rejected`, `returned` — "overdue" is a calculated display state on top of `borrowed`, not a separate status.