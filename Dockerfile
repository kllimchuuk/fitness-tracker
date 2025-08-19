FROM python:3.13-slim

WORKDIR /config

COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install -r requirements-dev.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]