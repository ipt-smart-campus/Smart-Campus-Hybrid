FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# comando real é definido por serviço no compose.yml (command: [...])
CMD ["python", "-u", "-m", "billing.main"]