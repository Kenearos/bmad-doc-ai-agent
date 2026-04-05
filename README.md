# BMAD-Doc-AI Desktop Agent

Lokaler Ordner-Watcher der neue Dokumente automatisch an deinen BMAD-Doc-AI Server hochlädt.

## Installation

```bash
pip install -e .
```

## Konfiguration

```bash
cp .env.example .env
nano .env  # Email, Passwort, Ordner eintragen
```

## Starten

```bash
bmad-agent
```

Oder direkt:
```bash
python -m bmad_agent.cli
```

## Was passiert

1. Agent verbindet sich mit deinem BMAD-Server
2. Überwacht den konfigurierten Ordner (Standard: `~/Documents/BMAD-Eingang`)
3. Neue PDFs, Bilder, DOCX werden automatisch hochgeladen
4. Nach Upload: Datei wird in `verarbeitet/` verschoben
5. Bei Fehler: Datei wird in `fehler/` verschoben

## Ordner-Struktur

```
BMAD-Eingang/
├── rechnung.pdf          ← Neue Datei → wird hochgeladen
├── verarbeitet/
│   └── rechnung.pdf      ← Nach erfolgreichem Upload
└── fehler/
    └── kaputt.xyz        ← Bei Fehler
```
