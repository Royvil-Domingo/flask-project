# Equipment Borrowing and Return System

A Flask web app for tracking equipment availability and borrowing transactions.

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
   Then open `.env` and replace `SECRET_KEY` with your own generated value:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Leave `DATABASE_URL` as-is — it defaults to a local SQLite file, no extra setup needed.

5. **Create the database and an admin account**
   ```bash
   set FLASK_APP=run.py        # Windows
   export FLASK_APP=run.py     # macOS/Linux
   flask seed-admin
   ```
   This prompts for an email, name, and password, and creates the first admin user.

6. **Run the app**
   ```bash
   python run.py
   ```
   Visit `http://127.0.0.1:5000` and log in with the admin account you just created.
