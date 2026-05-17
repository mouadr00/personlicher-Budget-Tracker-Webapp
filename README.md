# Persönlicher Budget Tracker Webapp

Browserbasierte Weiterentwicklung des CLI-Projekts **Persönlicher Budget Tracker**. Die App ist wie das Pizzeria-Referenzprojekt aufgebaut: NiceGUI als Frontend, serverseitige Python-Controller und Services, SQLite als Datenbank und SQLModel als ORM.

## Projektidee

Viele Studierende und Berufseinsteiger möchten Einnahmen und Ausgaben lokal verwalten, ohne externe Finanzsoftware zu nutzen. Diese Webapp macht den ursprünglichen Konsolen-Budgetplan als Browser-Anwendung nutzbar.

## User Stories

1. **Transaktion erfassen**
   Als Benutzer möchte ich Einnahmen und Ausgaben mit Datum, Kategorie, Betrag und Notiz erfassen.

2. **Monatsübersicht sehen**
   Als Benutzer möchte ich für einen ausgewählten Monat Einnahmen, Ausgaben und verfügbares Budget sehen.

3. **Grösste Ausgabenkategorie erkennen**
   Als Benutzer möchte ich sehen, wofür im Monat am meisten Geld ausgegeben wurde.

4. **Budgetplan speichern**
   Als Benutzer möchte ich geplante Einnahmen, Ausgaben und ein Sparziel pro Monat speichern.

5. **Bericht exportieren**
   Als Benutzer möchte ich einen Monatsbericht als PDF speichern.

6. **Passwortschutz verwenden**
   Als Benutzer möchte ich die App mit einem Passwort schützen und das Passwort später ändern.

## Funktionen

- Browser-App mit NiceGUI
- Passwort-Setup, Login und Passwortänderung
- Einnahmen und Ausgaben erfassen
- Kategorien verwalten
- Monatsfilter mit Transaktionstabelle
- Zusammenfassung: Einnahmen, Ausgaben, Saldo, grösste Ausgabenkategorie
- Budgetplan pro Monat
- PDF-Bericht mit ReportLab
- SQLite-Datenbank via SQLModel ORM
- Tests für Geschäftslogik und Datenbankzugriff

## Architektur

```text
budget_tracker_app/
├── application.py          # App-Komposition und NiceGUI-Start
├── domain/
│   └── models.py           # ORM-Modelle
├── data_access/
│   ├── db.py               # Datenbank-Fassade
│   ├── dao.py              # Repository/DAO-Klassen
│   └── seed.py             # Startkategorien
├── services/
│   ├── budget_service.py   # Businesslogik und Auswertungen
│   ├── password_service.py # Passwort-Hashing
│   ├── report_service.py   # PDF-Berichte
│   └── validation_service.py
└── ui/
    ├── controllers.py      # UI-Controller
    └── pages.py            # NiceGUI-Seiten
```

## Verwendete Bibliotheken

- `nicegui` für die Browser-Oberfläche
- `sqlmodel` und `sqlalchemy` für ORM und Datenbankzugriff
- `reportlab` für PDF-Berichte
- `pytest` für Tests

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Start

```powershell
python -m budget_tracker_app
```

Danach öffnet die App im Browser unter:

```text
http://localhost:8080
```

Beim ersten Start wird ein Passwort eingerichtet. Anschliessend muss man sich anmelden.

## Tests

```powershell
pytest
```

Die Tests erfüllen die geforderte Mindeststruktur:

- 12 Tests insgesamt
- 6 Unit-Tests in `tests/test_unit.py`
- 3 Datenbanktests in `tests/test_db.py`
- 3 Integrationstests in `tests/test_integration.py`

## Projektanforderungen SS26

- **NiceGUI Browser-App:** Die App läuft im Browser, die UI wird serverseitig mit Python aufgebaut.
- **Objektorientierung:** Modelle, Services, Controller, DAOs und App-Komposition sind als Klassen strukturiert.
- **ORM/Datenbank:** Daten werden in SQLite gespeichert und über SQLModel verwaltet.
- **Validierung:** Datum, Betrag, Kategorie, Passwort und Budgetplan werden geprüft.
- **Dokumentation:** README beschreibt Ziel, Funktionen, Architektur und Bedienung.
