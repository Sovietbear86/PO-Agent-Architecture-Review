# Используем указанный базовый образ
FROM sberworks.ru/sbt/ci90000655_biprdct/slo/sberlinux-9-x86_64-ubi@sha256:0d3b95f7d2f10deb09b8596cb232d8440be75aed6976a38a2862bcfcfb660fbf

ENV NAME=mcp-swtr
ENV VERSION=v1.0.0
ENV PYTHON_VERSION=3.11
ENV VENDOR=SberLinux
ENV SUMMARY="MCP server ${NAME} ${VERSION} with Python ${PYTHON_VERSION}"
ENV DESCRIPTION="Container for running MCP server ${NAME} ${VERSION} on Python ${PYTHON_VERSION} \
    Powered by ${VENDOR} \
    based on SberLinux UBI image with installed python${PYTHON_VERSION}"

# Определяем переменные окружения для настройки модели и URL
ARG PORT=8000
ARG BASE_URL=""
ARG TOKEN

RUN dnf update -y && \
    dnf install -y --allowerasing \
    python3.11 \
    python3.11-pip \
    && dnf clean all

# Устанавливаем рабочую директорию
WORKDIR /app
COPY requirements.txt ./requirements.txt


# Устанавливаем зависимости Python
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt


COPY / .
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

ENV PORT=${PORT}
ENV TOKEN=${TOKEN}
ENV BASE_URL=${BASE_URL}

EXPOSE ${PORT}

# Запуск приложения с передачей параметров через переменные окружения
CMD ["python3.11", "mcp_server.py"]