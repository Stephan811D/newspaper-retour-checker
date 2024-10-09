# Basis-Image mit Python 3.9 verwenden
FROM python:3.9-slim

# Arbeitsverzeichnis in den Container setzen
WORKDIR /app

# Kopiere die Anforderungen (requirements) in den Container
COPY requirements.txt requirements.txt

# Installiere die Python-Abhängigkeiten
RUN pip install -r requirements.txt

# Kopiere den Rest der Anwendung in den Container
COPY . .

# Flask auf dem Standardport 5000 ausführen
EXPOSE 5000

# Befehl, um die App zu starten
CMD ["python", "app.py"]