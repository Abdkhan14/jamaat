import os

from dotenv import load_dotenv

# Must run before any local imports that read os.environ (e.g. scraping.llm creates
# the OpenAI client at import time from os.environ["OPENAI_API_KEY"]).
load_dotenv()

from observability import init_sentry

init_sentry()

from flask import Flask
from flask_cors import CORS

from config import Config
from models.prayerTimes import db
from routes import register_routes
from scheduler import start_scheduler


def create_app():
    app = Flask(__name__)

    allowed_origins = [
        o.strip()
        for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    app.config.from_object(Config)
    db.init_app(app)

    register_routes(app)

    with app.app_context():
        db.create_all()

    start_scheduler(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
