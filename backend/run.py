"""Local development entrypoint for the Flask app."""

from app import create_app


def main() -> None:
    app = create_app()
    app.run(host="0.0.0.0", static_files="static", port=5000, debug=True)


if __name__ == "__main__":
    main()
