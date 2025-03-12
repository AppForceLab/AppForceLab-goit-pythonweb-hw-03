FROM python:3.13

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root --no-interaction --no-ansi

COPY . /app

EXPOSE 3000

CMD ["poetry", "run", "python", "main.py"]