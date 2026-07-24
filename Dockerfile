# Step 1: Use an official lightweight Python image based on Linux Alpine
FROM python:3.11-slim

# Step 2: Set the working directory inside the container
WORKDIR /code

# Step 3: Copy the requirements file first (we will create this next)
COPY ./requirements.txt /code/requirements.txt

# Step 4: Install the Python dependencies inside the container
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Step 5: Copy your actual 'app' folder into the container
COPY ./app /code/app

# 🌟 NEW: Copy seed.py too, so `docker compose exec web_app python seed.py` works
COPY ./seed.py /code/seed.py

# Step 6: Tell the container to run FastAPI using Uvicorn when it starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
