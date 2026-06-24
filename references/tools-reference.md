# Slack MCP Tools — Full Reference

This file documents the typical Slack MCP tools in detail. Read this when you
need to understand parameter formats, edge cases, or response structure beyond
what the SKILL.md cheat sheet covers.

## Response format

All Slack MCP tools return a JSON array with a single object:
```json
[{"type": "text", "text": "<CSV or plain text>"}]
```

The `text` field is usually CSV-formatted with a header row. Parse it as CSV
to extract structured data.

### conversations_history response columns

```
MsgID,UserID,UserName,RealName,Channel,ThreadTs,Text,Time,Permalink,Reactions,BotName,FileCount,AttachmentIDs,HasMedia,Cursor
```

- **MsgID**: Message timestamp (e.g. `1782122340.462039`). Also the message's unique ID.
- **UserID**: Slack user ID (e.g. `U02DRDMRH7E`).
- **UserName**: Handle (e.g. `takehiro-miyao`).
- **RealName**: Display name (may be empty for bots).
- **Channel**: Channel ID.
- **ThreadTs**: The thread's parent message ts. If equal to MsgID, this message
  IS the thread parent. If different, this message is a reply in that thread.
  If empty, it's a standalone non-thread message.
- **Text**: Message text (may contain mentions like `<@U02E36L9LS0>`, URLs,
  markdown, quoted cross-thread references).
- **Time**: ISO 8601 timestamp (e.g. `2026-06-22T09:59:00Z`).
- **Permalink**: URL to the message (may be empty).
- **Reactions**: Emoji reactions with counts, pipe-separated
  (e.g. `eyes:1|100:1`). Empty if none.
- **BotName**: Bot name if the message was posted by a bot (e.g. `miyao-bot`).
- **FileCount**: Number of files attached.
- **AttachmentIDs**: File IDs with names in parentheses.
- **HasMedia**: `true`/`false`.
- **Cursor**: Pagination cursor. If non-empty, pass this as `cursor` to the
  next `conversations_history` call to get older messages. Must be the value
  of the last row's Cursor column.

### conversations_replies response

Same CSV format as history, but only contains messages within one thread.
The first row is the thread parent message, subsequent rows are replies in
chronological order.

### conversations_add_message response

Returns a confirmation text like:
`Successfully posted message to channel C09M108RUJW (ts=1782123993.325489)`

The `ts` value in the response is the new message's timestamp.

### reactions_add / reactions_remove response

`Successfully added :thumbsup: reaction to message <ts> in channel <id>`
or
`Successfully removed :thumbsup: reaction from message <ts> in channel <id>`

## Edge cases

### Mentions in message text
Slack mentions appear as `<@U02E36L9LS0>` in the Text field. To resolve to a
name, match the UserID against the UserID/UserName columns of other messages
in the same channel, or look at the context.

### Cross-thread references
Some messages contain forwarded references with format:
`<https://vnlabcenter.slack.com/archives/.../p...>. Author: <name>; Text: <content>; Footer: ...`
These are Slack's "share to thread" or cross-link previews. Extract the Author
and Text to understand what's being referenced.

### Bot messages
Bots (like `miyao-bot`, `github-review`, `slackbot`) post messages with
`BotName` set. These often contain formatted content (summaries, reminders,
PR notifications). They're still useful for summarization.

### Activity messages
By default, `conversations_history` excludes activity messages
(channel_join, channel_leave, etc.). Set `include_activity_messages: true`
if you need them.

### Pagination
When the Cursor column in the last row is non-empty, there are more messages
to fetch. Pass the cursor value as the `cursor` parameter to the next call.
Do NOT also pass `limit` when using `cursor` — it must be empty.

## Thread ts conversion (detailed)

The Slack archives URL encodes the message ts as `p` + digits with no dot:
`p1782269365692859`

To convert to the ts format used by the API:
1. Remove the leading `p`: `1782269365692859`
2. The ts is `<digits>.<last_6_digits>`: `1782269365.692859`

So: `p` + `XXXXXXXXXXX` (13+ digits) → `XXXXXXXXXX.XXXXXX` (insert dot
before the last 6 digits).

This works because Slack ts values are Unix timestamps with microsecond
precision (6 decimal places).
