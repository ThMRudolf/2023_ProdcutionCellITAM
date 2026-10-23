#!/usr/bin/env python3
"""
haas_q600_tcp.py — Q600-Test über Netzwerk für die Haas ST-10 (CHC)   v2

Schritt 1: Port-Scan. Zeigt, WAS hinter der IP steckt.
Schritt 2: Banner lesen. Verbinden, Telnet-Aushandlung beantworten und alles
           ausgeben, was das Gerät von sich aus sendet (Login-Prompt, Modellname).
Schritt 3: Q-Codes senden. Varianten "Q100" / "?Q100", CR LF / CR.
           Als gültig zählt NUR eine Antwort mit ETB (0x17) — so antwortet Haas-MDC.
Schritt 4 (optional, --watch): Q600 zyklisch abfragen.

Änderungen gegenüber v1
  - Telnet-Steuersequenzen (IAC, 0xFF ...) werden erkannt, beantwortet und
    herausgefiltert. v1 hielt b'\\xff\\xfb\\x03' fälschlich für eine Antwort.
  - Gültig nur mit ETB.
  - Geschlossene Verbindung wird gemeldet statt als leere Antwort angezeigt.
  - Mehr Ports (Webinterface, Lantronix, USR, Moxa RealCOM).

Nur Python-Standardbibliothek.

Aufruf
  python haas_q600_tcp.py 192.168.1.50
  python haas_q600_tcp.py 192.168.1.50 --port 23
  python haas_q600_tcp.py 192.168.1.50 --port 23 --var 5021 5023 3027 --watch 1
"""

import argparse
import socket
import time

STX, ETB = b"\x02", b"\x17"
IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
TELNET_OPT = {0: "BINARY", 1: "ECHO", 3: "SUPPRESS-GO-AHEAD", 24: "TERMINAL-TYPE",
              31: "WINDOW-SIZE", 32: "TERMINAL-SPEED", 34: "LINEMODE", 44: "COM-PORT (RFC 2217)"}

PORTS = {
    5051:  "Haas Q-Code-Server (NGC)",
    23:    "Telnet — Konsole eines Seriellservers ODER Datenkanal",
    80:    "Webinterface (Seriellserver-Konfiguration?)",
    443:   "Webinterface HTTPS",
    4000:  "Seriellserver-Datenport (div. Hersteller)",
    4001:  "Moxa NPort, Datenport 1 (TCP-Server-Modus)",
    4002:  "Moxa NPort, Datenport 2",
    950:   "Moxa Real-COM-Modus, Datenport",
    966:   "Moxa Real-COM-Modus, Steuerport",
    9999:  "Lantronix Konfigurations-Telnet",
    10001: "Lantronix Datenport",
    8234:  "USR-TCP232 Datenport",
    20108: "USR-TCP232 Datenport (alternativ)",
    502:   "Modbus TCP",
    8082:  "MTConnect-Agent (Haas NGC)",
    5000:  "MTConnect-Agent (cppagent)",
    21:    "FTP",
    139:   "NetBIOS",
    445:   "SMB",
}
QCODE_CANDIDATES = (5051, 4001, 4002, 4000, 950, 10001, 8234, 20108, 23)
DEFAULT_VARS = [5021, 5023, 3027, 3026, 3001]


class Closed(Exception):
    pass


class Conn:
    """TCP-Verbindung, die Telnet-Aushandlung beantwortet (alles ablehnen) und
    Steuersequenzen aus dem Datenstrom entfernt."""

    def __init__(self, host, port, timeout):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.telnet_log = []
        self._pending = b""

    def close(self):
        self.sock.close()

    def _filter(self, data):
        data = self._pending + data
        self._pending = b""
        out = bytearray()
        i = 0
        while i < len(data):
            b = data[i]
            if b != IAC:
                out.append(b)
                i += 1
                continue
            if i + 1 >= len(data):
                self._pending = data[i:]
                break
            cmd = data[i + 1]
            if cmd == IAC:                       # escaped 0xFF
                out.append(IAC)
                i += 2
            elif cmd in (DO, DONT, WILL, WONT):
                if i + 2 >= len(data):
                    self._pending = data[i:]
                    break
                opt = data[i + 2]
                name = {DO: "DO", DONT: "DONT", WILL: "WILL", WONT: "WONT"}[cmd]
                self.telnet_log.append(f"{name} {TELNET_OPT.get(opt, opt)}")
                if cmd == DO:
                    self.sock.sendall(bytes([IAC, WONT, opt]))
                elif cmd == WILL:
                    # SGA annehmen ist harmlos und von vielen Servern erwartet
                    reply = DO if opt == 3 else DONT
                    self.sock.sendall(bytes([IAC, reply, opt]))
                i += 3
            elif cmd == SB:
                end = data.find(bytes([IAC, SE]), i)
                if end < 0:
                    self._pending = data[i:]
                    break
                self.telnet_log.append(f"SB {TELNET_OPT.get(data[i + 2], data[i + 2])}")
                i = end + 2
            else:
                i += 2
        return bytes(out)

    def recv(self, timeout):
        self.sock.settimeout(timeout)
        try:
            chunk = self.sock.recv(1024)
        except socket.timeout:
            return b""
        if not chunk:
            raise Closed()
        return self._filter(chunk)

    def drain(self, seconds):
        buf = bytearray()
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            buf += self.recv(max(0.01, end - time.perf_counter()))
        return bytes(buf)

    def ask(self, cmd, eol, timeout):
        self.drain(0.05)
        t0 = time.perf_counter()
        self.sock.sendall(cmd.encode("ascii") + eol)
        buf = bytearray()
        end = t0 + timeout
        while time.perf_counter() < end:
            buf += self.recv(max(0.01, end - time.perf_counter()))
            if ETB in buf:
                buf += self.drain(0.05)
                break
        return bytes(buf), (time.perf_counter() - t0) * 1000


def clean(raw):
    return raw.replace(STX, b"").replace(ETB, b"").decode("ascii", "replace").replace(">", "").strip()


def scan(host, timeout=0.8):
    open_ports = []
    for port, desc in PORTS.items():
        s = socket.socket()
        s.settimeout(timeout)
        try:
            if s.connect_ex((host, port)) == 0:
                open_ports.append(port)
                print(f"  {port:>5}  offen   {desc}")
        finally:
            s.close()
    if not open_ports:
        print("  keine der geprüften Ports offen")
    return open_ports


def banner(host, port, timeout):
    print(f"\n2) Banner {host}:{port} (3 s zuhören, nichts senden)")
    try:
        c = Conn(host, port, timeout)
        data = c.drain(3.0)
        c.close()
    except Closed:
        print("  Gegenstelle hat die Verbindung sofort geschlossen.")
        return
    except OSError as e:
        print(f"  Verbindung fehlgeschlagen: {e}")
        return
    print(f"  Telnet-Aushandlung: {', '.join(c.telnet_log) or 'keine'}")
    text = data.decode("ascii", "replace").strip()
    print(f"  Text:  {text[:300]!r}" if text else "  Text:  (nichts)")
    if any(k in text.lower() for k in ("login", "password", "username", "nport", "moxa", "lantronix", "console")):
        print("  → Das ist eine Konfigurationskonsole, kein Datenkanal zur Steuerung.")


def find_syntax(host, port, timeout):
    for eol in (b"\r\n", b"\r"):
        for prefix in ("", "?"):
            cmd = f"{prefix}Q100"
            try:
                c = Conn(host, port, timeout)
                c.drain(0.5)  # Aushandlung abwickeln, Banner verwerfen
                raw, ms = c.ask(cmd, eol, timeout)
            except Closed:
                print(f"  {cmd!r:<8} EOL={eol!r:<8} Verbindung von Gegenstelle geschlossen")
                continue
            ok = ETB in raw and not any(t in clean(raw).upper() for t in ("UNKNOWN", "INVALID"))
            print(f"  {cmd!r:<8} EOL={eol!r:<8} {ms:7.1f} ms  {'GÜLTIG' if ok else '–':<7} roh={raw[:60]!r}")
            if ok:
                return c, prefix, eol
            c.close()
    return None, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("--port", type=int)
    ap.add_argument("--var", type=int, nargs="+", default=DEFAULT_VARS)
    ap.add_argument("--timeout", type=float, default=2.0)
    ap.add_argument("--watch", type=float, metavar="SEK")
    args = ap.parse_args()

    if args.port:
        candidates = [args.port]
    else:
        print(f"1) Port-Scan {args.host}")
        open_ports = scan(args.host)
        if 80 in open_ports or 443 in open_ports:
            print(f"  → http://{args.host} im Browser öffnen: Die Konfigurationsseite nennt Hersteller und Modell.")
        candidates = [p for p in QCODE_CANDIDATES if p in open_ports]

    for port in candidates:
        banner(args.host, port, args.timeout)
        print(f"\n3) Q-Code-Test {args.host}:{port}")
        c, prefix, eol = find_syntax(args.host, port, args.timeout)
        if c is None:
            print("  Keine gültige Haas-Antwort (mit ETB) auf diesem Port.")
            continue
        with c.sock:
            print(f"  → Syntax: Präfix {prefix!r}, Zeilenende {eol!r}\n")
            try:
                for v in args.var:
                    raw, ms = c.ask(f"{prefix}Q600 {v}", eol, args.timeout)
                    print(f"  Q600 {v:<5} {ms:7.1f} ms  {clean(raw)!r:<36} roh={raw!r}")
                if args.watch:
                    print(f"\n4) Live alle {args.watch} s — Achse verfahren / Spindel starten. Strg+C beendet.")
                    while True:
                        vals = []
                        for v in args.var:
                            raw, _ = c.ask(f"{prefix}Q600 {v}", eol, args.timeout)
                            vals.append(f"#{v}={clean(raw).split(',')[-1].strip()}")
                        print(time.strftime("%H:%M:%S"), "  ".join(vals))
                        time.sleep(args.watch)
            except Closed:
                print("  Verbindung während der Abfrage geschlossen.")
            except KeyboardInterrupt:
                pass
        return
    print("\nKein Port lieferte eine gültige Q-Code-Antwort.")


if __name__ == "__main__":
    main()
