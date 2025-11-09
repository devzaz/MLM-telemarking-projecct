# MLM Telemarking Project — Quick start (dev)

## 1. Clone
git clone https://github.com/devzaz/MLM-telemarking-projecct.git
cd MLM-telemarking-projecct

## 2. Python venv & install
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

## 3. Environment
cp .env.example .env
# Edit .env and set SECRET_KEY and other values.

## 4. Database & run
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

## 5. Docker (optional, dev)
# build & run
docker-compose up --build

## Notes
- Do NOT commit `.env` or `db.sqlite3` to the repo.
- For production use PostgreSQL — update `DATABASE_URL` accordingly.
