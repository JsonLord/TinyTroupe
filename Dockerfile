FROM python:3.10-slim

WORKDIR /app

# Install git since pip installing from a git repository or -e . may require it,
# although -e . here refers to a local directory, it's good practice for general python projects.
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY pyproject.toml .
COPY setup.p[y] .
COPY setup.cf[g] .

# Copy all files for -e . installation
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]