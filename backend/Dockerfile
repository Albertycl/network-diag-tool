FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn
COPY . .
ARG PORT
ENV PORT=${PORT}
EXPOSE ${PORT}
# Create tables (and default templates for admin) on start, then serve
CMD ["sh", "-c", "python init_db_script.py && exec gunicorn -w 2 -b 0.0.0.0:${PORT} app:app"]
