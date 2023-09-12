FROM python:3.11-slim
RUN pip install "poetry==1.6.1"

WORKDIR /code
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . /code

CMD ["uvicorn", "proxy.main:app", "--host", "0.0.0.0", "--port", "8080"]
