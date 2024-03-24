import os

BACKEND_BASE_URL = os.environ["TL_BACKEND_BASE_URL"]
STORAGE_DIR = os.environ["TL_STORAGE_DIR"]

SESSION_TTL_HOURS = 10
DATABASE_DSN = os.environ["TL_DATABASE_DSN"]

AUTO_RELOAD = bool(os.environ.get("TL_AUTO_RELOAD"))

PROMETHEUS_NAME_PREFIX = os.environ.get("TL_PROMETHEUS_NAME_PREFIX")
PROMETHEUS_PORT = int(os.environ.get("TL_PROMETHEUS_PORT", 9100))

SENTRY_DSN = os.environ["TL_SENTRY_DSN"]
ENVIRONMENT = os.environ.get("TL_ENVIRONMENT", "unknown")

TIME_RESERVE_COEF = float(os.environ["TL_TIME_RESERVE_COEF"])
