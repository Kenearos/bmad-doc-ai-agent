# BMAD-Doc-AI Desktop Agent

Lokaler Ordner-Watcher der neue Dokumente automatisch an deinen BMAD-Doc-AI Server hochlädt.

## Installation

```bash
pip install -e .
```

## Erster Start

```bash
bmad-agent
```

Beim ersten Start öffnet sich ein Setup-Wizard:
1. **Server** — URL deines BMAD-Servers
2. **Anmeldung** — Google oder E-Mail/Passwort
3. **Ordner** — Welche Ordner überwacht werden sollen

## Zwei Modi

### CLI-Modus (Terminal / NAS / Server)
```bash
bmad-agent
```
Läuft im Terminal, zeigt Upload-Status an. Ideal für NAS, Raspberry Pi, Server.

### Tray-Modus (Desktop)
```bash
bmad-agent --tray
```
Zeigt ein System-Tray-Icon mit:
- Grün = läuft, Rot = Fehler, Gelb = pausiert
- Rechtsklick: Pausieren, Einstellungen, Beenden
- Desktop-Notifications bei Upload

### Einstellungen ändern
```bash
bmad-agent --setup
```

## Als Dienst auf NAS/Server

### Linux (systemd)
```bash
cat > ~/.config/systemd/user/bmad-agent.service << EOF
[Unit]
Description=BMAD-Doc-AI Agent
After=network.target

[Service]
ExecStart=$(which bmad-agent)
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user enable --now bmad-agent
```

### Synology NAS
Task Scheduler → Create → Triggered Task → `bmad-agent`

## Ordner-Struktur

```
Überwachter-Ordner/
├── neue-rechnung.pdf     ← Wird automatisch hochgeladen
├── verarbeitet/
│   └── neue-rechnung.pdf ← Nach erfolgreichem Upload
└── fehler/
    └── kaputt.xyz        ← Bei Upload-Fehler
```

## Config

Gespeichert in `~/.config/bmad-agent/config.json`:
```json
{
  "server_url": "https://docai.pixel-by-design.de",
  "auth_method": "google",
  "email": "deine@email.de",
  "watch_dirs": [
    "~/Documents/BMAD-Eingang",
    "~/NAS/Dokumente"
  ],
  "move_after_upload": true,
  "file_extensions": [".pdf", ".png", ".jpg", ".docx"]
}
```
