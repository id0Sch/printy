"""`python -m backend` -> run the API server."""
import uvicorn


def main() -> None:
    uvicorn.run("backend.api:app", host="127.0.0.1", port=7777, reload=False)


if __name__ == "__main__":
    main()
