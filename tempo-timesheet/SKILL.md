---
name: tempo-timesheet
description: "View and create Tempo timesheet worklogs (log time / timesheets) against Jira issues, for yourself, other people, or a whole team. Use this skill whenever the user mentions: logging time, logging work, log work, timesheet, timesheets, tempo, worklog, worklogs, my hours, what did I log, how much time did I spend, check my timesheet, fill my timesheet, time tracking, time entry, log hours, book time, team timesheet, team hours, who logged, what did the team log, or wants to see/create/edit weekly or daily time entries in Tempo. Also trigger when the user references a Tempo URL (tempo-app, io.tempo.jira) or asks to add time to a Jira ticket. This skill reads and writes via the Tempo REST API and resolves Jira issue keys to IDs via the Atlassian MCP."
---

# Tempo Timesheet

View and create worklogs in Tempo Timesheets (the `io.tempo.jira` app on Jira Cloud). Tempo stores its data separately from Jira's native worklogs, so this skill uses the Tempo REST API (`api.tempo.io/4`) rather than the Atlassian MCP's `addWorklogToJiraIssue` tool.

## Prerequisites

Two pieces of information are needed, both obtained once and then reused:

1. **Tempo API token** — stored in the `TEMPO_TOKEN` environment variable. The user creates it in Tempo → Settings → Data Access → API Integration → New Token (Read scope for viewing, Read+Write for creating). If `TEMPO_TOKEN` is not set, tell the user how to get it (see "Onboarding" below) and stop — do not guess or proceed without it.

2. **Atlassian account ID** — stored in the `TEMPO_ACCOUNT_ID` environment variable (format: `712020:xxxx-xxxx-xxxx-xxxx`). Obtain it via the `atlassian` MCP server's `atlassianUserInfo` tool (the `account_id` field). If the MCP server is not configured or the tool is unavailable, ask the user for their account ID.

The bundled script `scripts/tempo.py` reads both from env vars (or accepts them as `--account-id` flags). Always source the user's env file before running the script. A common pattern is a `.env` file in the project or home directory — try `source .env 2>/dev/null` or check `~/.env`, `~/.config/tempo/.env` if the env vars are not already exported.

## The script

`scripts/tempo.py` is a self-contained Python 3 CLI (stdlib only, no pip install needed). Run it with `python3 <skill-dir>/scripts/tempo.py <command> [options]`.

### Commands

| Command | Purpose |
|---------|---------|
| `week` | View current week's worklogs (Mon–Sun), grouped by day with totals |
| `today` | View today's worklogs only |
| `view --from YYYY-MM-DD --to YYYY-MM-DD` | View an arbitrary date range |
| `view --user <accountId>` | View another user's worklogs (needs their Atlassian account ID) |
| `team [--team-id NUM] [--from ...] [--to ...]` | View a whole team's worklogs, grouped by user. Auto-detects team if only one exists. |
| `members [--team-id NUM]` | List team members with their account IDs (use to look up someone's ID) |
| `create --issue-id NUM --time "2h" [--date ...] [--start HH:MM] [--desc ...]` | Create a worklog |
| `delete --worklog-id NUM` | Delete a worklog (use when correcting mistakes) |

Time format for `--time`: `2h`, `30m`, `1h30m`, `1.5h`, `90m`, `4d` (1d = 8h).

## Workflow: Viewing worklogs

This is the simple case — just run the script.

1. Ensure `TEMPO_TOKEN` and `TEMPO_ACCOUNT_ID` are set (source the env file).
2. Run `python3 scripts/tempo.py week` (or `today`, or `view` with a range).
3. Present the output to the user in a readable table. The script already groups by date and shows per-day + week totals, so you can relay it mostly as-is, optionally reformatting into a Markdown table for clarity.

If the user asks about a specific day, use `view --from DATE --to DATE`. If they ask "this week" or "this month" without specifying, default to the current work week (Mon–Sun).

## Workflow: Viewing other people's / team worklogs

Tempo supports viewing worklogs for other users and whole teams, as long as the token has permission (the Tempo "Read" scope typically grants access to team members' worklogs).

### View a specific person

You need their **Atlassian account ID** (format `712020:xxxx-...` or `557058:xxxx-...`). To find it:

1. Run `python3 scripts/tempo.py members` to list team members with their account IDs (auto-detects the team if there's only one).
2. Match the person by their account ID. If you only know their name/email, the account ID alone won't tell you who they are — you may need to cross-reference with the Jira REST API or ask the user.

Then: `python3 scripts/tempo.py view --user <accountId> --from YYYY-MM-DD --to YYYY-MM-DD`

### View a whole team

If the org uses Tempo Teams, you can fetch all worklogs for a team in one call, grouped by user:

```
python3 scripts/tempo.py team --from 2026-06-22 --to 2026-06-26
```

This auto-detects the team if there's only one. If there are multiple teams, it lists them with their IDs — re-run with `--team-id NUM`. The output groups worklogs by user (with account IDs) then by date, so you can see who logged what.

### Notes on team views

- The output shows account IDs, not names (Tempo's team-members endpoint doesn't include display names). If the user wants names, you can resolve account IDs to names via the Jira REST API (`/rest/api/3/user?accountId=...`) if a Jira API token is available, or via the Atlassian MCP if it exposes a user-lookup tool.
- Team worklogs can be large (38 members × multiple entries/day). The script paginates automatically, but the output can be long. Consider narrowing the date range or summarizing by user totals only.

## Workflow: Creating a worklog

Creating a worklog requires the **numeric Jira issue ID**, not the issue key (e.g. `OSHIETE-5801`). Tempo's API only accepts the numeric ID. Resolve it as follows:

1. **Resolve the issue key → numeric ID.** Call the `atlassian` MCP tool `getJiraIssue` with:
   - `cloudId`: the user's site URL (e.g. `https://jisedaisystem.atlassian.net`) or UUID. If unknown, call `getAccessibleAtlassianResources` first.
   - `issueIdOrKey`: the issue key the user gave you (e.g. `OSHIETE-5801`)
   
   The response includes a numeric `id` field — that is what Tempo needs.

2. **Confirm with the user before creating.** State clearly what you are about to log: issue key, time, date, description. Example:
   > "I'll log 2h to OSHIETE-5801 for today (2026-06-26) starting 09:00 with description 'Working on work item'. OK?"
   
   Wait for confirmation. Logging time is a write action that affects the user's timesheet and billing — never skip this step.

3. **Run the create command:**
   ```
   python3 scripts/tempo.py create --issue-id <NUM> --time "2h" --date 2026-06-26 --start 09:00:00 --desc "Working on work item"
   ```

4. **Report the result.** The script prints the new worklog ID and a confirmation line. Relay it to the user.

### Batch creates

If the user wants to log multiple entries at once (e.g. "log 2h on OSHIETE-5801, 1.5h on OSHIETE-4222, 30m on VNLAB-5 for today"), resolve all issue keys first (you can call `getJiraIssue` in parallel for each), present a summary table of what will be logged, get one confirmation, then run the `create` command for each entry.

## Workflow: Deleting / correcting a worklog

If the user says they logged the wrong thing and want to undo it:

1. Run `week` or `today` to show current worklogs — each line includes `wid=<ID>`.
2. Ask which entry to delete (confirm the ID).
3. Run `python3 scripts/tempo.py delete --worklog-id <ID>`.
4. Optionally help them re-create the correct entry.

## Onboarding (when TEMPO_TOKEN is missing)

If `TEMPO_TOKEN` is not set, guide the user through getting one:

1. Open Tempo in their Jira instance (the `tempo-app` URL).
2. Go to **Settings** (gear icon in Tempo sidebar) → **Data Access** → **API Integration**.
3. Click **New Token**, name it (e.g. `devin-cli`), set expiry, grant **Read** scope (and **Write** if they want to create/delete worklogs).
4. Copy the token — it's only shown once.
5. Save it: `echo 'export TEMPO_TOKEN="paste-token"' >> ~/.bashrc && source ~/.bashrc` (or into a `.env` file).

For `TEMPO_ACCOUNT_ID`: call `atlassianUserInfo` via the MCP and tell the user to also export it:
```
echo 'export TEMPO_ACCOUNT_ID="712020:xxxx-xxxx-xxxx-xxxx"' >> ~/.bashrc && source ~/.bashrc
```

## Security notes

- The Tempo token is a personal credential with the same data access as the user. Never print the full token in output, never commit it to git, and never send it to any endpoint other than `api.tempo.io`.
- If the user stored the token in a `.env` file inside a git repo, warn them to add `.env` to `.gitignore`.
- Always confirm before creating or deleting worklogs — these affect timesheets and potentially billing.

## Examples

**User:** "check my timesheet this week"
→ Run `python3 scripts/tempo.py week`, present the grouped output.

**User:** "log 2h on OSHIETE-5801 for today"
→ Resolve OSHIETE-5801 via `getJiraIssue` MCP → confirm with user → `python3 scripts/tempo.py create --issue-id <NUM> --time "2h"`.

**User:** "I logged 3h on the wrong ticket yesterday, fix it"
→ Run `view --from <yesterday> --to <yesterday>` → identify the wrong entry's `wid` → confirm → `delete --worklog-id <WID>` → offer to re-create on the correct ticket.
