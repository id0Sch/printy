"""`python -m backend` -> run the API server."""

import logging

import uvicorn


def main() -> None:
    # Make logger.info / logger.exception in our code visible. Uvicorn's own
    # access logs go through its own loggers; this only configures the root
    # logger so the "printy" logger in api.py actually emits.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    uvicorn.run("backend.api:app", host="127.0.0.1", port=7777, reload=False)


if __name__ == "__main__":
    main()
