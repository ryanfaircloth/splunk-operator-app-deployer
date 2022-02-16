FROM python:3.10.0-bullseye as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app

FROM base as builder
RUN pip install --upgrade pip ;\
    pip install poetry 

COPY poetry.lock pyproject.toml /app/
WORKDIR /app
RUN poetry config virtualenvs.in-project true ;\
    poetry install ;\
    . /app/.venv/bin/activate


FROM base as final

COPY --from=builder /app/.venv /app/.venv
COPY deploy.py /app/
