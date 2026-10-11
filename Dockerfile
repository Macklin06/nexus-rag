FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .

# Install project dependencies before copying application source.
# Read dependencies directly from pyproject.toml to avoid duplication.
RUN python -c "import subprocess, sys, tomllib; p = tomllib.load(open('pyproject.toml', 'rb')); subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', *p['project']['dependencies']])"

COPY src ./src
COPY worker.py .

# Install the local package without reinstalling its dependencies.
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000

CMD ["uvicorn", "rag_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]