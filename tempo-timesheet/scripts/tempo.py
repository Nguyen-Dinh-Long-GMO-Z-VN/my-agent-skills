#!/usr/bin/env python3
"""Tempo Timesheets CLI — view, create, and delete Tempo worklogs.

Requires TEMPO_TOKEN env var (Tempo API token from Tempo > Settings > Data Access > API Integration).
Requires TEMPO_ACCOUNT_ID env var (Atlassian account ID, e.g. 712020:xxxx-xxxx-xxxx-xxxx).
  The agent can obtain this once via the atlassian MCP `atlassianUserInfo` tool.

Usage:
  tempo.py view [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--account-id ID] [--user ID]
  tempo.py create --issue-id NUM --time "2h" [--date YYYY-MM-DD] [--start HH:MM] [--desc TEXT] [--account-id ID]
  tempo.py delete --worklog-id NUM
  tempo.py today [--account-id ID]          # view today only (self)
  tempo.py week [--account-id ID]           # view current week (Mon-Sun, self)
  tempo.py team [--team-id NUM] [--from YYYY-MM-DD] [--to YYYY-MM-DD]   # team worklogs
  tempo.py members [--team-id NUM]          # list team members (account IDs)

Time format: "2h", "30m", "1h30m", "1.5h", "90m". 1d = 8h = 28800s.
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from datetime import date, timedelta

API_BASE = "https://api.tempo.io/4"


def get_token():
    tok = os.environ.get("TEMPO_TOKEN")
    if not tok:
        sys.exit("ERROR: TEMPO_TOKEN env var not set. Get a token from Tempo > Settings > Data Access > API Integration.")
    return tok


def get_account_id(arg_val):
    aid = arg_val or os.environ.get("TEMPO_ACCOUNT_ID")
    if not aid:
        sys.exit("ERROR: account ID not provided. Pass --account-id or set TEMPO_ACCOUNT_ID env var. "
                 "The agent can get it via the atlassian MCP `atlassianUserInfo` tool (field account_id).")
    return aid


def api_request(method, path, body=None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} {e.reason}\n{err_body}")


def parse_time_to_seconds(s):
    """Parse '2h', '30m', '1h30m', '1.5h', '90m', '4d' → seconds. 1d=8h."""
    s = s.strip().lower().replace(" ", "")
    total = 0
    num = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        elif ch in "hmd":
            if not num:
                sys.exit(f"ERROR: bad time format '{s}'")
            val = float(num)
            if ch == "h":
                total += int(val * 3600)
            elif ch == "m":
                total += int(val * 60)
            elif ch == "d":
                total += int(val * 8 * 3600)
            num = ""
        else:
            sys.exit(f"ERROR: bad time format '{s}'")
    if num:
        sys.exit(f"ERROR: bad time format '{s}' (trailing number without unit)")
    if total == 0:
        sys.exit(f"ERROR: time must be > 0")
    return total


def fmt_hours(secs):
    h = secs / 3600
    return f"{h:.2f}h"


def fetch_worklogs(path):
    """Fetch worklogs with automatic pagination."""
    results = []
    offset = 0
    while True:
        sep = "&" if "?" in path else "?"
        paged = f"{path}{sep}offset={offset}&limit=250"
        data = api_request("GET", paged)
        page = data.get("results", [])
        results.extend(page)
        meta = data.get("metadata", {})
        # Check if there's a next page
        if not data.get("metadata", {}).get("next"):
            break
        offset += len(page)
        if not page:
            break
    return results


def print_worklogs(results, title_prefix, from_str, to_str, group_by_user=False):
    """Print worklogs grouped by date (and optionally by user)."""
    print(f"# {title_prefix} — {from_str} → {to_str}")
    print(f"Total worklogs: {len(results)}\n")

    if group_by_user:
        # Group by author then by date
        by_user = {}
        for w in results:
            aid = w.get("author", {}).get("accountId", "unknown")
            by_user.setdefault(aid, []).append(w)
        grand_total = 0
        for aid in sorted(by_user):
            print(f"## User: {aid}")
            _print_grouped(by_user[aid])
            user_total = sum(w["timeSpentSeconds"] for w in by_user[aid])
            grand_total += user_total
            print(f"  → User total: {fmt_hours(user_total)}\n")
        print(f"## Grand total: {fmt_hours(grand_total)}")
    else:
        _print_grouped(results)
        total = sum(w["timeSpentSeconds"] for w in results)
        print(f"## Total: {fmt_hours(total)}")


def _print_grouped(worklogs):
    by_date = {}
    for w in worklogs:
        by_date.setdefault(w["startDate"], []).append(w)
    for d in sorted(by_date):
        print(f"### {d}")
        day_total = 0
        for w in by_date[d]:
            secs = w["timeSpentSeconds"]
            day_total += secs
            desc = (w.get("description") or "").replace("\n", " ")[:90]
            wid = w.get("tempoWorklogId", "?")
            iid = w["issue"]["id"]
            author = w.get("author", {}).get("accountId", "")
            author_tag = f" user={author}" if author else ""
            print(f"  - {fmt_hours(secs):>7} | wid={wid} issueId={iid}{author_tag} | {desc}")
        print(f"  → Day total: {fmt_hours(day_total)}\n")


def cmd_view(args):
    # Determine whose worklogs to fetch
    target_user = getattr(args, "user", None)
    if target_user:
        # View another user's worklogs
        aid = target_user
    else:
        aid = get_account_id(args.account_id)

    if args.from_date:
        from_str = args.from_date
        to_str = args.to_date or from_str
    else:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        from_str = monday.isoformat()
        to_str = (monday + timedelta(days=6)).isoformat()

    encoded = urllib.parse.quote(aid, safe="")
    path = f"/worklogs/user/{encoded}?from={from_str}&to={to_str}"
    results = fetch_worklogs(path)
    label = "Another user's timesheet" if target_user else "Tempo Timesheet"
    print_worklogs(results, label, from_str, to_str, group_by_user=False)


def cmd_create(args):
    aid = get_account_id(args.account_id)
    secs = parse_time_to_seconds(args.time)
    d = args.date or date.today().isoformat()
    st = args.start_time or "09:00:00"
    body = {
        "authorAccountId": aid,
        "issueId": int(args.issue_id),
        "timeSpentSeconds": secs,
        "startDate": d,
        "startTime": st,
    }
    if args.desc:
        body["description"] = args.desc
    result = api_request("POST", "/worklogs/", body)
    print(f"✓ Created worklog {result.get('tempoWorklogId')} — {fmt_hours(secs)} on issueId={args.issue_id} for {d}")
    print(f"  URL: {result.get('self', '')}")


def cmd_delete(args):
    api_request("DELETE", f"/worklogs/{args.worklog_id}")
    print(f"✓ Deleted worklog {args.worklog_id}")


def cmd_team(args):
    team_id = args.team_id
    if team_id is None:
        # Auto-discover: list teams and use the first one
        data = api_request("GET", "/teams?limit=50")
        teams = data.get("results", [])
        if not teams:
            sys.exit("ERROR: No Tempo teams found. Pass --team-id explicitly.")
        if len(teams) == 1:
            team_id = teams[0]["id"]
            print(f"Using team: {teams[0]['name']} (id={team_id})\n")
        else:
            print("Multiple teams found. Specify --team-id:")
            for t in teams:
                print(f"  id={t['id']}  {t['name']}")
            return

    if args.from_date:
        from_str = args.from_date
        to_str = args.to_date or from_str
    else:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        from_str = monday.isoformat()
        to_str = (monday + timedelta(days=6)).isoformat()

    path = f"/worklogs/team/{team_id}?from={from_str}&to={to_str}"
    results = fetch_worklogs(path)
    print_worklogs(results, f"Team {team_id} timesheet", from_str, to_str, group_by_user=True)


def cmd_members(args):
    team_id = args.team_id
    if team_id is None:
        data = api_request("GET", "/teams?limit=50")
        teams = data.get("results", [])
        if not teams:
            sys.exit("ERROR: No Tempo teams found. Pass --team-id explicitly.")
        if len(teams) == 1:
            team_id = teams[0]["id"]
        else:
            print("Multiple teams found. Specify --team-id:")
            for t in teams:
                print(f"  id={t['id']}  {t['name']}")
            return

    data = api_request("GET", f"/teams/{team_id}/members?limit=100")
    members = data.get("results", [])
    print(f"# Team {team_id} — {len(members)} members\n")
    print(f"{'Account ID':<55} | Role")
    print("-" * 80)
    for m in members:
        aid = m["member"]["accountId"]
        role = m.get("memberships", {}).get("active", {}).get("role", {}).get("name", "?")
        print(f"{aid:<55} | {role}")


def main():
    p = argparse.ArgumentParser(description="Tempo Timesheets CLI")
    sub = p.add_subparsers(dest="command", required=True)

    pv = sub.add_parser("view", help="View worklogs for a date range (default: current week)")
    pv.add_argument("--from-date", dest="from_date", help="Start date YYYY-MM-DD")
    pv.add_argument("--to-date", dest="to_date", help="End date YYYY-MM-DD")
    pv.add_argument("--account-id", help="Atlassian account ID (or set TEMPO_ACCOUNT_ID) — defaults to your own")
    pv.add_argument("--user", help="View ANOTHER user's worklogs by their Atlassian account ID")

    pt = sub.add_parser("today", help="View today's worklogs (self)")
    pt.add_argument("--account-id", help="Atlassian account ID (or set TEMPO_ACCOUNT_ID)")

    pw = sub.add_parser("week", help="View current week's worklogs (Mon-Sun, self)")
    pw.add_argument("--account-id", help="Atlassian account ID (or set TEMPO_ACCOUNT_ID)")

    pteam = sub.add_parser("team", help="View worklogs for a whole team (grouped by user)")
    pteam.add_argument("--team-id", dest="team_id", type=int, help="Tempo team ID (auto-detects if only one team exists)")
    pteam.add_argument("--from-date", dest="from_date", help="Start date YYYY-MM-DD (default: this week)")
    pteam.add_argument("--to-date", dest="to_date", help="End date YYYY-MM-DD")

    pmem = sub.add_parser("members", help="List team members with their account IDs")
    pmem.add_argument("--team-id", dest="team_id", type=int, help="Tempo team ID (auto-detects if only one team)")

    pc = sub.add_parser("create", help="Create a worklog")
    pc.add_argument("--issue-id", required=True, help="Numeric Jira issue ID (NOT the key — resolve via getJiraIssue MCP first)")
    pc.add_argument("--time", required=True, help='Time spent, e.g. "2h", "30m", "1h30m"')
    pc.add_argument("--date", help="Date YYYY-MM-DD (default: today)")
    pc.add_argument("--start-time", dest="start_time", help="Start time HH:MM:SS (default: 09:00:00)")
    pc.add_argument("--desc", help="Description / comment")
    pc.add_argument("--account-id", help="Atlassian account ID (or set TEMPO_ACCOUNT_ID)")

    pd = sub.add_parser("delete", help="Delete a worklog")
    pd.add_argument("--worklog-id", dest="worklog_id", required=True, help="Tempo worklog ID (tempoWorklogId)")

    args = p.parse_args()

    if args.command in ("today", "week", "view"):
        if args.command == "today":
            today = date.today().isoformat()
            args.from_date = today
            args.to_date = today
        elif args.command == "week":
            args.from_date = None
            args.to_date = None
        cmd_view(args)
    elif args.command == "create":
        cmd_create(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "team":
        cmd_team(args)
    elif args.command == "members":
        cmd_members(args)


if __name__ == "__main__":
    main()
