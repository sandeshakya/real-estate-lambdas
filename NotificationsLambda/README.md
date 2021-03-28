# Web Scraper Notification

---

Sends notifications to subscribed members of topic for new listings

## How to install

- run `pip install virtualenv` if virtual environment is not installed
- `python -m venv venv`
- activate virtual environment `source venv/Scripts/activate`
- run `pip install -r requirements.txt`

Copy `.env.stub` to `.env` file and configure environment variables

## How to Run Locally

run `python-lambda-local -f handler -e .env src/handler.py event/event.json -t 300`
