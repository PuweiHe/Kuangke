"""Serve synthetic branch metrics from SQLite to a small browser UI."""

import argparse
import json
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from metrics import summarize, validate_records


ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent


class MetricsRepository:
    def __init__(self, records):
        validate_records(records)
        self.connection = sqlite3.connect(":memory:", check_same_thread=False)
        self.lock = threading.Lock()
        self.connection.execute("""CREATE TABLE branch_revenue (
            branch_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            revenue_million REAL NOT NULL CHECK (revenue_million >= 0),
            PRIMARY KEY (branch_id, year)
        )""")
        self.connection.executemany(
            "INSERT INTO branch_revenue (branch_id, year, revenue_million) VALUES (?, ?, ?)",
            [(row["branch_id"], row["year"], row["revenue_million"]) for row in records],
        )
        self.connection.commit()

    def years(self):
        with self.lock:
            rows = self.connection.execute(
                "SELECT DISTINCT year FROM branch_revenue ORDER BY year DESC"
            ).fetchall()
        return [row[0] for row in rows]

    def report(self, year, branch_id=None):
        with self.lock:
            rows = self.connection.execute(
                """SELECT branch_id, year, revenue_million FROM branch_revenue
                   WHERE year IN (?, ?) ORDER BY year, branch_id""",
                (year, year - 1),
            ).fetchall()
        records = [dict(branch_id=row[0], year=row[1], revenue_million=row[2]) for row in rows]
        summary = summarize(records, year)
        selected = next((row for row in summary["branches"] if row["branch_id"] == branch_id), None)
        if branch_id and selected is None:
            raise LookupError("Branch is unavailable for the selected year")
        summary["selected_branch"] = selected
        return summary

    def close(self):
        with self.lock:
            self.connection.close()


def make_handler(repository):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, payload):
            body = json.dumps(payload, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlsplit(self.path)
            if url.path == "/healthz":
                self.respond(200, {"status": "ok", "synthetic": True})
                return
            if url.path == "/api/years":
                self.respond(200, {"years": repository.years(), "synthetic": True})
                return
            if url.path == "/api/metrics":
                query = parse_qs(url.query, keep_blank_values=True)
                if any(len(values) != 1 for values in query.values()) or set(query) - {
                    "year",
                    "branch_id",
                }:
                    self.respond(400, {"error": "Use one year and optional branch_id"})
                    return
                try:
                    year_text = query["year"][0]
                    if len(year_text) != 4 or not year_text.isascii() or not year_text.isdecimal():
                        raise ValueError()
                    year = int(year_text)
                    if year not in repository.years():
                        raise LookupError("Year is unavailable")
                    branch_id = query.get("branch_id", [None])[0]
                    if branch_id is not None and (not branch_id or len(branch_id) > 64):
                        raise ValueError()
                    self.respond(200, repository.report(year, branch_id))
                except (KeyError, ValueError):
                    self.respond(400, {"error": "Invalid year or branch_id"})
                except LookupError as exc:
                    self.respond(404, {"error": str(exc)})
                return
            files = {
                "/": ("index.html", "text/html"),
                "/app.js": ("app.js", "text/javascript"),
                "/style.css": ("style.css", "text/css"),
            }
            if url.path not in files:
                if url.path.startswith("/api/"):
                    self.respond(404, {"error": "Unknown API endpoint"})
                    return
                self.send_error(404)
                return
            filename, mime = files[url.path]
            body = (ASSETS / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; frame-ancestors 'none'; base-uri 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Synthetic branch analytics browser demo")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    records = json.loads((ROOT / "examples/branches.json").read_text())
    repository = MetricsRepository(records)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(repository))
    print(f"Open http://127.0.0.1:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        repository.close()


if __name__ == "__main__":
    main()
