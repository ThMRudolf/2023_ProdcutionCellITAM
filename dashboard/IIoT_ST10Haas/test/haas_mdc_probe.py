#!/usr/bin/env python3
"""
haas_mdc_probe.py — Phase-0-Test für die Haas ST-10 (Classic Haas Control)

Prüft, welche Q-Codes die Steuerung beantwortet, insbesondere ob Q600
(Makrovariablen lesen) funktioniert, und misst die Antwortlatenz je Code.

Voraussetzungen an der Maschine
  Setting 143 (Machine Data Collection) = ON
  RS-232: Baudrate = Setting 11 (ST-10 ITAM: 115200, per --baud), 7 Datenbits, Parität Even, 1 Stoppbit, XON/XOFF
  (Settings 11, 12, 13, 14, 37 an der Steuerung gegenprüfen)

Installation
  pip install pyserial

Aufruf
  python haas_mdc_probe.py --port COM3 --baud 115200   # USB-RS-232 unter Windows
  python haas_mdc_probe.py --port /dev/ttyUSB0         # Linux / Raspberry Pi
  python haas_mdc_probe.py --port socket://192.168.1.50:4001   # Moxa im TCP-Server-Modus
  python haas_mdc_probe.py --simulate                  # ohne Maschine, testet nur das Skript
  python haas_mdc_probe.py --port COM3 --repeat 20     # Latenzstatistik mit 20 Wiederholungen

Ergebnis
  Tabelle auf der Konsole + mdc_probe_<Zeitstempel>.json mit allen Rohantworten.
  Die JSON-Datei ist zugleich der erste Mitschnitt für replay.py in Phase 1.
"""

import argparse
import json
import statistics
import sys
import time
from datetime import datetime

import serial

STX, ETB = b"\x02", b"\x17"

# Q-Codes aus der Haas-MDC-Dokumentation. Ob die ST-10 sie alle kennt,
# ist genau das, was dieser Test herausfinden soll.
QCODES = [
    ("Q100", "Seriennummer"),
    ("Q101", "Softwareversion"),
    ("Q102", "Modell"),
    ("Q104", "Modus"),
    ("Q200", "Werkzeugwechsel gesamt"),
    ("Q201", "aktives Werkzeug"),
    ("Q300", "Einschaltzeit"),
    ("Q301", "Bewegungszeit"),
    ("Q303", "letzte Zykluszeit"),
    ("Q304", "vorherige Zykluszeit"),
    ("Q402", "M30-Zähler 1"),
    ("Q403", "M30-Zähler 2"),
    ("Q500", "Programm / Status / Teile"),
]

# Makrovariablen für Q600. Nummern im Bedienhandbuch der ST-10 gegenprüfen;
# eine Variable, die die Steuerung nicht kennt, ist hier ein Ergebnis, kein Fehler.
MACROS = [
    (5021, "Maschinenposition X"),
    (5022, "Maschinenposition Y (ST-10: keine Y-Achse, Erwartung leer/0)"),
    (5023, "Maschinenposition Z"),
    (5041, "Werkstückposition X"),
    (5043, "Werkstückposition Z"),
    (3026, "Werkzeug in Arbeitsposition"),
    (3027, "Spindeldrehzahl"),
    (3001, "Millisekunden-Timer (sollte sich bei jeder Abfrage ändern)"),
]

NEGATIVE = ("UNKNOWN", "INVALID", "ERROR")


def open_port(port: str, timeout: float, baud: int) -> serial.SerialBase:
    """Öffnet echte COM-Ports und socket:// URLs mit denselben Parametern."""
    ser = serial.serial_for_url(port, do_not_open=True)
    ser.baudrate = baud
    ser.bytesize = serial.SEVENBITS
    ser.parity = serial.PARITY_EVEN
    ser.stopbits = serial.STOPBITS_ONE
    ser.xonxoff = True
    ser.timeout = timeout
    ser.open()
    return ser


def read_response(ser, timeout: float) -> bytes:
    """Liest bis ETB. Ohne ETB innerhalb des Timeouts kommt zurück, was da ist."""
    buf = bytearray()
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buf += chunk
            if ETB in buf:
                # Nach ETB folgen meist CR LF und das Prompt-Zeichen '>'.
                time.sleep(0.01)
                buf += ser.read(ser.in_waiting)
                break
    return bytes(buf)


def clean(raw: bytes) -> str:
    """Entfernt STX/ETB/Prompt und gibt den Nutzinhalt als Text zurück."""
    text = raw.replace(STX, b"").replace(ETB, b"").decode("ascii", errors="replace")
    return text.replace(">", "").strip()


def query(ser, cmd: str, timeout: float, eol: bytes):
    ser.reset_input_buffer()
    t0 = time.perf_counter()
    ser.write(cmd.encode("ascii") + eol)
    ser.flush()
    raw = read_response(ser, timeout)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    payload = clean(raw)
    if not raw:
        status = "keine Antwort"
    elif any(tok in payload.upper() for tok in NEGATIVE):
        status = "abgelehnt"
    elif ETB not in raw:
        status = "unvollständig"
    else:
        status = "ok"
    return {"cmd": cmd, "status": status, "payload": payload,
            "raw_hex": raw.hex(" "), "latency_ms": round(dt_ms, 1)}


def detect_eol(ser, timeout: float) -> bytes:
    """Testet, ob die Steuerung CR oder CR LF als Zeilenende erwartet."""
    for eol in (b"\r\n", b"\r"):
        if query(ser, "Q100", timeout, eol)["status"] == "ok":
            return eol
    return b"\r\n"


# ---------------------------------------------------------------------------
# Simulator — nur um das Skript ohne Maschine durchzutesten
# ---------------------------------------------------------------------------
class FakeHaas:
    """Antwortet wie eine CHC, die Q600 kennt. Keine Aussage über die echte ST-10."""
    in_waiting = 0

    def __init__(self):
        self._out = b""
        self.t0 = time.time()

    def reset_input_buffer(self): self._out = b""
    def flush(self): pass
    def close(self): pass

    def write(self, data: bytes):
        cmd = data.decode().strip()
        answers = {"Q100": "SERIAL NUMBER, 1234567", "Q101": "SOFTWARE VERSION, M18.24",
                   "Q102": "MODEL, ST-10", "Q104": "MODE, MEM", "Q201": "USED TOOL, 3",
                   "Q402": "M30 #1, 117",
                   "Q500": "PROGRAM, O01234, IDLE, PARTS, 117"}
        if cmd.startswith("Q600"):
            var = int(cmd.split()[1])
            val = {5021: 42.18, 5023: -12.405, 3027: 1850}.get(var, 0.0)
            if var == 3001:
                val = (time.time() - self.t0) * 1000
            ans = f"MACRO, {val:.4f}"
        else:
            ans = answers.get(cmd, "UNKNOWN")
        time.sleep(0.02)
        self._out = STX + ans.encode() + ETB + b"\r\n>"
        self.in_waiting = len(self._out)

    def read(self, n=1):
        n = max(n, 1)
        chunk, self._out = self._out[:n], self._out[n:]
        self.in_waiting = len(self._out)
        return chunk


def main():
    ap = argparse.ArgumentParser(description="Q-Code-Test für Haas CHC (ST-10)")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--port", help="COM3, /dev/ttyUSB0 oder socket://IP:PORT")
    src.add_argument("--simulate", action="store_true", help="ohne Maschine")
    ap.add_argument("--baud", type=int, default=38400, help="muss Setting 11 entsprechen (ST-10 ITAM: 115200)")
    ap.add_argument("--timeout", type=float, default=1.0, help="Sekunden je Anfrage")
    ap.add_argument("--repeat", type=int, default=5, help="Wiederholungen für Latenzstatistik")
    args = ap.parse_args()

    ser = FakeHaas() if args.simulate else open_port(args.port, args.timeout, args.baud)
    try:
        eol = b"\r\n" if args.simulate else detect_eol(ser, args.timeout)
        print(f"Zeilenende: {eol!r}\n")

        commands = [(c, d) for c, d in QCODES] + [(f"Q600 {v}", d) for v, d in MACROS]
        results = []
        print(f"{'Befehl':<11} {'Status':<14} {'Median ms':>9} {'p95 ms':>7}  Antwort / Bedeutung")
        print("-" * 96)
        for cmd, desc in commands:
            runs = [query(ser, cmd, args.timeout, eol) for _ in range(args.repeat)]
            lat = sorted(r["latency_ms"] for r in runs if r["status"] == "ok")
            first = runs[0]
            med = f"{statistics.median(lat):.1f}" if lat else "–"
            p95 = f"{lat[min(len(lat) - 1, int(0.95 * len(lat)))]:.1f}" if lat else "–"
            print(f"{cmd:<11} {first['status']:<14} {med:>9} {p95:>7}  {first['payload'][:40]:<40} ({desc})")
            results.append({"cmd": cmd, "desc": desc, "runs": runs})
            time.sleep(0.05)
    finally:
        ser.close()

    q600 = [r for r in results if r["cmd"].startswith("Q600")]
    q600_ok = any(run["status"] == "ok" for r in q600 for run in r["runs"])
    timer = next((r for r in q600 if r["cmd"] == "Q600 3001"), None)
    timer_vals = {run["payload"] for run in timer["runs"]} if timer else set()

    print("\nBewertung")
    print(f"  Q600 beantwortet:            {'ja' if q600_ok else 'NEIN — Achspositionen über MDC nicht verfügbar'}")
    if timer:
        live = len(timer_vals) > 1
        print(f"  #3001 ändert sich (live?):   {'ja' if live else 'nein — Werte prüfen, evtl. gecacht'}")
    ok_lat = [run["latency_ms"] for r in results for run in r["runs"] if run["status"] == "ok"]
    if ok_lat:
        med = statistics.median(ok_lat)
        print(f"  Median-Latenz gesamt:        {med:.1f} ms")
        print(f"  Schnellgruppe (X, Z, n, Q500 = 4 Abfragen) theoretisch: {1000 / (4 * med):.1f} Hz")

    out = f"mdc_probe_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"port": args.port or "simulate", "baud": args.baud, "eol": eol.decode().encode("unicode_escape").decode(),
                   "timestamp": datetime.now().isoformat(), "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\nRohdaten: {out}")


if __name__ == "__main__":
    sys.exit(main())
