# Web Scraper for SaskHouses

---

Scrapes [SaskHouses](https://saskhouses.com/) for houses using the provided environment variables.

If `ENV` is `DEV`, prints house information to terminal, if `ENV` is `PROD` inserts house information to AWS DynamoDB Table.

**Setting `ENV` to `PROD` requires DynamoDB table name to be inserted into**

## How to install

- run `pip install virtualenv` if virtual environment is not installed
- `python -m venv venv`
- activate virtual environment `source venv/Scripts/activate`
- run `pip install -r requirements.txt`

Copy `.env.stub` to `.env` file and configure environment variables

## How to Run Locally

run `python-lambda-local -f handler -e .env src/index.py event/event.json -t 300`
