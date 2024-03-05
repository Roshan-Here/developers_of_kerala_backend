# FROM python:3.11.0

# ENV PYTHONUNBUFFERED 1

# WORKDIR /

# COPY poetry.lock pyproject.toml ./
# RUN pip install --upgrade pip && \
#     pip install poetry && \
#     poetry config virtualenvs.create false

# ARG DEV=false
# RUN if [ "$DEV" = "true" ] ; then poetry install ; else poetry install --no-dev --no-root ; fi

# COPY . .

# ENV PYTHONPATH "${PYTHONPATH}:/"

# EXPOSE 8080
# CMD uvicorn app.main:app --host 0.0.0.0 --port 8080

# Use the official Python image as the base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the poetry files to the container
COPY pyproject.toml poetry.lock /app/

# Install Poetry
RUN pip install poetry

# Install project dependencies using Poetry
RUN poetry install --no-root --no-interaction

# Copy the rest of the application code to the container
COPY . /app/

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
