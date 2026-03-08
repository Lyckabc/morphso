FROM python:3.11-slim
WORKDIR /app
ARG BUILD_DATE
ARG BUILD_VERSION
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.version=$BUILD_VERSION
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py setup_db.py infisical_client.py infisical_router.py ./
EXPOSE 8013
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
