import os
import sys
import threading
import webbrowser
from pathlib import Path


def bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def configure_database() -> Path:
    data_dir = application_dir() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    database_path = (data_dir / "matriz_competencias.db").resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    return database_path


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    backend_resources = bundle_root() / "backend"
    config = Config(str(backend_resources / "alembic.ini"))
    config.set_main_option("script_location", str(backend_resources / "alembic"))
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
    command.upgrade(config, "head")


def open_browser() -> None:
    webbrowser.open("http://127.0.0.1:8000")


def main() -> None:
    database_path = configure_database()
    run_migrations()
    from app.main import app
    import uvicorn

    print(f"Base de datos: {database_path}")
    print("Aplicación: http://127.0.0.1:8000")
    threading.Timer(1.2, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
