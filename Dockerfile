FROM python:3.10-slim
ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Note: the timeout is set to 0 to disable the timeouts of the workers to allow
# Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 0 tinylocs.app:app
