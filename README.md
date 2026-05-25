# Persoenlicher Budget Tracker Webapp

Browserbasierte Weiterentwicklung des CLI-Projekts **Persoenlicher Budget Tracker**. Die App ist wie das Pizzeria-Referenzprojekt aufgebaut: NiceGUI als Frontend, serverseitige Python-Controller und Services, SQLite als Datenbank und SQLModel als ORM.

## Projektidee

Viele Studierende und Berufseinsteiger moechten Einnahmen, Ausgaben, Sparziele und Monatsbudgets lokal verwalten, ohne externe Finanzsoftware zu nutzen. Diese Webapp macht den urspruenglichen Konsolen-Budgetplan als Browser-Anwendung nutzbar und zeigt direkt ein realistisches Beispielbudget mit Seed-Daten.

## User Stories

1. **Buchung erfassen**
   Als Benutzer moechte ich Einnahmen, Ausgaben und Umbuchungen mit Datum, Kategorie, Betrag und Notiz erfassen.

2. **Sparkonto umbuchen**
   Als Benutzer moechte ich Geld vom Budget zum Sparkonto oder vom Sparkonto zurueck ins Budget umbuchen.

3. **Monatsuebersicht sehen**
   Als Benutzer moechte ich Einnahmen, Ausgaben, genutztes Budget, Restbudget und Sparziel-Fortschritt fuer einen Monat sehen.

4. **Ausgaben analysieren**
   Als Benutzer moechte ich die groessten Kategorien, Prozentanteile, Diagramme und einen Monatsvergleich sehen.

5. **Buchungen suchen, filtern und bearbeiten**
   Als Benutzer moechte ich Buchungen nach Text, Typ und Kategorie filtern sowie bestehende Eintraege editieren oder loeschen.

6. **Budgetplan speichern**
   Als Benutzer moechte ich geplante Einnahmen, Ausgaben und ein Sparziel pro Monat speichern.

7. **Berichte exportieren**
   Als Benutzer moechte ich Monatsberichte als PDF und Buchungsdaten als CSV exportieren.

8. **Passwortschutz verwenden**
   Als Benutzer moechte ich die App mit einem Passwort schuetzen und das Passwort spaeter aendern.

## Funktionen

- Browser-App mit NiceGUI
- Passwort-Setup, Login und Passwortaenderung
- Realistische Seed-Daten mit 12 Monatsbudgets und ueber 100 Beispielbuchungen
- Einnahmen, Ausgaben und Umbuchungen erfassen
- Umbuchungsrichtungen: `Budget zu Sparkonto` und `Sparkonto zu Budget`
- Kategorien direkt beim Erfassen einer Buchung hinzufuegen
- Buchungen editieren und loeschen
- Monatsfilter mit Transaktionstabelle
- Suche und Filter nach Text, Typ und Kategorie
- Dashboard mit Einnahmen, Ausgaben, Restbudget, groesster Kategorie, Monatsvergleich und Netto-Sparen
- Kuchendiagramm fuer Ausgaben-Verteilung
- Balkendiagramm fuer Monatsvergleich
- Budget-Limite mit Warnung ab 80 Prozent und bei Ueberschreitung
- Sparziel-Fortschritt und einfache automatische Spartipps
- PDF-Bericht mit ReportLab
- CSV-Export fuer Buchungen
- SQLite-Datenbank via SQLModel ORM
- Tests fuer Geschaeftslogik, Datenbankzugriff und Integration

## Bedienung

Beim ersten Start wird ein Passwort eingerichtet. Danach kann man sich anmelden und die App lokal im Browser nutzen.

Im Dashboard wird ein Monat ausgewaehlt. Danach zeigt die App Kennzahlen, Diagramme, Budgetwarnungen, Spartipps und die Buchungen dieses Monats.

Neue Buchungen werden im Bereich **Neue Buchung** erfasst:

- `Einnahme`: Geld kommt ins Budget.
- `Ausgabe`: Geld wird ausgegeben.
- `Umbuchung`: Geld wird zwischen Budget und Sparkonto verschoben.

Bei einer Umbuchung wird automatisch die Kategorie `Sparkonto` angezeigt. Die Richtung bestimmt die Wirkung:

- `Budget zu Sparkonto`: reduziert das verfuegbare Budget und erhoeht den Sparfortschritt.
- `Sparkonto zu Budget`: erhoeht das verfuegbare Budget und reduziert den Netto-Sparbetrag.

## Architektur

```text
budget_tracker_app/
|-- application.py          # App-Komposition und NiceGUI-Start
|-- domain/
|   `-- models.py           # ORM-Modelle
|-- data_access/
|   |-- db.py               # Datenbank-Fassade und Schema-Migration
|   |-- dao.py              # Repository/DAO-Klassen
|   `-- seed.py             # Start- und Demo-Daten
|-- services/
|   |-- budget_service.py   # Businesslogik und Auswertungen
|   |-- password_service.py # Passwort-Hashing
|   |-- report_service.py   # PDF- und CSV-Export
|   `-- validation_service.py
`-- ui/
    |-- controllers.py      # UI-Controller
    `-- pages.py            # NiceGUI-Seiten
```

## Verwendete Bibliotheken

- `nicegui` fuer die Browser-Oberflaeche
- `sqlmodel` und `sqlalchemy` fuer ORM und Datenbankzugriff
- `reportlab` fuer PDF-Berichte
- `pytest` fuer Tests

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Falls die mitgelieferte lokale Umgebung verwendet wird:

```powershell
.\.venv312\Scripts\Activate.ps1
```

## Start

```powershell
python -m budget_tracker_app
```

Danach die App im Browser oeffnen:

```text
http://localhost:8080
```

## Tests

```powershell
python -m pytest
```

Die Tests erfuellen die geforderte Mindeststruktur:

- 12 Tests insgesamt
- 6 Unit-Tests in `tests/test_unit.py`
- 3 Datenbanktests in `tests/test_db.py`
- 3 Integrationstests in `tests/test_integration.py`

## Projektanforderungen SS26

- **NiceGUI Browser-App:** Die App laeuft im Browser, die UI wird serverseitig mit Python aufgebaut.
- **Objektorientierung:** Modelle, Services, Controller, DAOs und App-Komposition sind als Klassen strukturiert.
- **ORM/Datenbank:** Daten werden in SQLite gespeichert und ueber SQLModel verwaltet.
- **Validierung:** Datum, Betrag, Kategorie, Passwort, Umbuchung und Budgetplan werden geprueft.
- **Seed-Daten:** Die App zeigt beim Start ein vollstaendiges Beispielbudget.
- **Analysen:** Dashboard, Diagramme, Monatsvergleich, Budgetwarnung und Spartipps helfen beim Budget-Tracking.
- **Export:** Monatsberichte koennen als PDF und CSV erstellt werden.
- **Dokumentation:** README beschreibt Ziel, Funktionen, Architektur, Bedienung und Tests.

## Moegliche Erweiterungen

Folgende Punkte sind bewusst als Erweiterung eingeordnet, weil sie ein groesseres Benutzer- und Rechtekonzept brauchen:

- Rollen-System, z.B. Admin darf bearbeiten, Viewer darf nur ansehen
- Benutzerprofil mit mehreren Benutzern
- Benachrichtigungen mit gespeicherten Regeln
