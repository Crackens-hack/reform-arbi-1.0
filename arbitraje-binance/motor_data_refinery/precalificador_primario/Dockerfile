FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-mysql-client \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libmariadb-dev \
    mycli \
    less \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🧠 Agregamos solo el alias, como corresponde
RUN echo "alias db='mycli -h \$DB_HOST -u \$DB_USER -p\$DB_PASSWORD \$DB_NAME'" >> /root/.bashrc
RUN echo "alias db2='mycli -h \$DB2_HOST -u \$DB2_USER -p\$DB2_PASSWORD \$DB2_NAME'" >> /root/.bashrc