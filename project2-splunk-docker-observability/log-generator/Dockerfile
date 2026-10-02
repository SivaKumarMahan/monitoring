FROM python:3.13-slim

RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY generator.py .

USER 10001
CMD ["python", "-u", "generator.py"]
