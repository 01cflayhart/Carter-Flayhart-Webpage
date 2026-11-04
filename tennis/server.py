"""Read-only local HTTP API and dashboard. Bind to loopback by default."""
import argparse
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlsplit, unquote

from .engine import SURFACES, parse_date, significant, statistics
from .update import ROOT, read_json


class Application:
    def __init__(self, root=ROOT, data_dir="data"):
        self.root = Path(root)
        self.data_dir = self.root / data_dir
        self.tours = {}
        self.lock = threading.Lock()
        self.stamp = None
        self.snapshot = None
        self.players = {}

    def load(self):
        path = self.data_dir / "snapshot.json"
        with self.lock:
            stamp = path.stat().st_mtime_ns
            if stamp != self.stamp:
                snapshot = read_json(path)
                self.snapshot, self.players = snapshot, {p["id"]: p for p in snapshot["players"]}
                self.stamp = stamp
            return self.snapshot, self.players

    def api(self, path, q):
        if "tour" in q:
            tour = q["tour"][0]
            if tour not in ("ATP", "WTA"):
                raise ValueError("Tour must be ATP or WTA")
            with self.lock:
                if tour not in self.tours:
                    self.tours[tour] = Application(self.root, "data/current/"+tour)
            return self.tours[tour].api(path, {k: v for k, v in q.items() if k != "tour"})
        snapshot, players = self.load()
        value = lambda key, default="": q.get(key, [default])[0]
        if path == "/api/meta":
            meta = {k: v for k, v in snapshot.items() if k != "players"}
            report = snapshot.get("backtest") or read_json(self.root / "reports" / "backtest.json")
            if report.get("model_version") != snapshot["model_version"] or report.get("end_inclusive") != snapshot["as_of"] or report.get("rating_config") != snapshot["rating_config"] or report.get("source_revision") != snapshot["source"]["revision"]:
                report = {}
            meta.update(player_count=len(players), staleness_days=(date.today() - parse_date(snapshot.get("latest_result",snapshot["as_of"]))).days,
                        update_status=read_json(self.data_dir / "status.json"),
                        backtest=snapshot.get("backtest",report))
            return meta
        basis, window = value("basis", "atp"), value("window", "year")
        surface = value("surface", "Overall")
        if basis not in ("atp", "power") or window not in ("year", "recent") or surface not in ("Overall", *SURFACES):
            raise ValueError("Invalid comparison basis, time window or surface")
        no_ret = value("no_ret", "0") == "1"
        try:
            offset = max(0, int(value("offset", "0")))
            limit = min(100, max(1, int(value("limit", "50"))))
            sample = max(0, int(value("sample", "0")))
        except ValueError as error:
            raise ValueError("Invalid pagination or minimum sample") from error
        cutoff = parse_date(snapshot["recent_start_exclusive"] if window == "recent" else snapshot["window_start_exclusive"])
        if path.startswith("/api/players/"):
            parts = path.strip("/").split("/")
            player = players.get(unquote(parts[2]))
            if player is None:
                raise KeyError("Player not found")
            if len(parts) == 3:
                result = {k: v for k, v in player.items() if k != "history"}
                result["selected_stats"] = statistics(player["history"], cutoff, basis, no_ret, surface)
                result["selected_stats_year"] = statistics(player["history"], parse_date(snapshot["window_start_exclusive"]), basis, no_ret, surface)
                result["selected_stats_recent"] = statistics(player["history"], parse_date(snapshot["recent_start_exclusive"]), basis, no_ret, surface)
                result["all_stats"] = {"year": statistics(player["history"], parse_date(snapshot["window_start_exclusive"]), basis, no_ret),
                                       "recent": statistics(player["history"], parse_date(snapshot["recent_start_exclusive"]), basis, no_ret)}
                return result
            if len(parts) != 4 or parts[3] != "results":
                raise KeyError("Endpoint not found")
            rows = [r for r in player["history"] if r["date"] > cutoff.isoformat() and (not no_ret or not r["retired"]) and (surface == "Overall" or r["surface"] == surface)]
            if value("significant", "1") == "1":
                rows = [r for r in rows if significant(r["own_" + basis], r["opp_" + basis], r["won"])]
            return {"total": len(rows), "offset": offset, "results": rows[offset:offset + limit]}
        if path != "/api/rankings":
            raise KeyError("Endpoint not found")
        search, flag, tier = value("q").casefold().strip(), value("flag"), value("tier")
        output = []
        for p in snapshot["players"]:
            if search not in (p["name"] + " " + p["country"]).casefold():
                continue
            if value("active", "0") == "1" and p["inactive_days"] >= 42:
                continue
            if p["matches"] < sample or (flag and flag not in p["flags"]) or (tier and tier not in p["tiers"]):
                continue
            stats = statistics(p["history"], cutoff, basis, no_ret, surface) if no_ret or surface != "Overall" else p["stats"][basis][window]
            compact = {k: v for k, v in p.items() if k not in ("history", "stats")}
            compact["selected_stats"] = stats
            compact["form"] = [r["won"] for r in p["history"][:5]][::-1]
            compact["selected_rank"] = p["rank"] if surface == "Overall" else p["surfaces"][surface]["rank"]
            compact["selected_rating"] = p["rating"] if surface == "Overall" else p["surfaces"][surface]["rating"]
            output.append(compact)
        sort = value("sort", "rank")
        valid = ("rank", "rating", "atp_rank", "atp_points", "name", "movement", "matches", "age", "inactive_days")
        metric = value("metric", "overall")
        if sort == "record" and metric not in ("overall", "top50", "similar", "better", "worse", "unknown", "Unknown", *SURFACES):
            raise ValueError("Invalid record metric")
        if sort not in valid and sort != "record" and not (sort.startswith("surface:") and sort[8:] in SURFACES):
            raise ValueError("Invalid sort")
        descending = value("direction", "desc" if sort in ("rating", "movement", "matches", "atp_points", "record") else "asc") == "desc"
        def sort_value(p):
            if sort == "rank":
                return p["selected_rank"]
            if sort == "rating":
                return p["selected_rating"]
            if sort.startswith("surface:"):
                return p["surfaces"][sort[8:]]["rank"]
            if sort == "record":
                w, l = p["selected_stats"][metric]
                return w / (w + l) if w + l else None
            return p.get(sort)
        present, missing = [p for p in output if sort_value(p) is not None], [p for p in output if sort_value(p) is None]
        present.sort(key=lambda p: p["id"])
        present.sort(key=sort_value, reverse=descending)
        ordered = present + sorted(missing, key=lambda p: p["id"])
        return {"total": len(ordered), "offset": offset, "players": ordered[offset:offset + limit]}


def handler_for(app):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(app.root / "web"), **kwargs)

        def end_headers(self):
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' https: data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            super().end_headers()

        def json_response(self, data, code=200):
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
            try:
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # Fast filter changes cancel old fetches, not publications.
                return

        def do_GET(self):
            parsed = urlsplit(self.path)
            if not parsed.path.startswith("/api/"):
                if parsed.path not in ("/", "/index.html", "/style.css", "/app.js", "/favicon.svg", "/runtime.js", "/static-api.js"):
                    self.send_error(404)
                    return
                return super().do_GET()
            try:
                return self.json_response(app.api(parsed.path, parse_qs(parsed.query)))
            except FileNotFoundError:
                return self.json_response({"error": "No publication yet. Run python3 -m tennis.update."}, 503)
            except KeyError as error:
                return self.json_response({"error": str(error)}, 404)
            except ValueError as error:
                return self.json_response({"error": str(error)}, 400)
            except OSError:
                return self.json_response({"error": "Publication unavailable. Check updater logs."}, 503)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), handler_for(Application()))
    print(f"Court Current → http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
