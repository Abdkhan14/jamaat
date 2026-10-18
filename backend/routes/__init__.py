from .health import health_bp
from .prayer_times import prayer_times_bp
from .mosque_requests import mosque_requests_bp


def register_routes(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(prayer_times_bp)
    app.register_blueprint(mosque_requests_bp)
