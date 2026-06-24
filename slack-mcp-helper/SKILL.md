---
name: slack-mcp-helper
description: >-
  Smooth, efficient operation of the Slack MCP server tools — reading channel
  history, fetching thread replies, posting/cross-posting messages, replying in
  threads, adding reactions, searching content, handling truncated output,
  checking unread mentions, detecting group mentions (@here/@channel/@subteam),
  and summarizing discussions. Use this skill whenever the user asks to read,
  search, summarize, post, reply, react, cross-post, or find unread mentions
  in Slack, or pastes a Slack URL (app.slack.com/client/... or
  <workspace>.slack.com/archives/...), or mentions "channel", "thread", "Slack",
  "tin nhắn", "thảo luận", "post lên", "tóm tắt channel", "reply", "reaction",
  "like", "tag", "mention", "chưa đọc", "ai tag mình", "@here", "@channel",
  "@subteam", "group mention", or any similar phrasing — even if they don't
  explicitly say "use the Slack MCP". Trigger aggressively for any Slack-related
  task.
---

# Slack MCP Helper

You have access to a Slack MCP server (typically named `slack`). This skill
makes working with it faster and more reliable by documenting the exact tool
schemas, URL-parsing rules, batching patterns, and common workflows — so you
don't waste round-trips on tool discovery or hit avoidable parameter errors.

## Available tools (cheat sheet)

These are the tools exposed by the `slack` MCP server. **You still must call
`mcp_list_tools` with `server_name: "slack"` once at the start of a session**
to confirm the exact tool names and schemas for the current workspace —
MCP servers can vary slightly. But the list below is a reliable reference for
what's typically available and the parameter names that matter.

| Tool | Purpose | Key params |
|------|---------|------------|
| `channels_list` | List all workspace channels | `channel_types` (required): comma-separated from `mpim,im,public_channel,private_channel`; `query`, `limit` |
| `channels_me` | List channels you've joined | `channel_types` (optional), `limit` |
| `conversations_history` | Get messages from a channel | `channel_id` (required), `limit` (e.g. `"1d"`, `"50"`, `"30d"`), `cursor` |
| `conversations_replies` | Get messages in a thread | `channel_id` (required), `thread_ts` (required, format `1234567890.123456`), `cursor`, `limit` |
| `conversations_add_message` | Post a message | `channel_id` (required), `text`, `content_type` (`text/markdown` default, or `text/plain`), `thread_ts` (optional, to reply in thread), `blocks` (raw Block Kit JSON, overrides text) |
| `conversations_join` | Join a public channel | `channel_id` |
| `conversations_leave` | Leave a channel | `channel_id` |
| `conversations_mark` | Mark channel/DM as read | `channel_id`, `ts` (optional) |
| `reactions_add` | Add emoji reaction to a message | `channel_id`, `timestamp` (the message ts), **`emoji`** (e.g. `"thumbsup"`, `"heart"`) — NOT `name` |
| `reactions_remove` | Remove emoji reaction | `channel_id`, `timestamp`, **`emoji`** |

**Common parameter-name pitfalls** (these cause real errors):
- `reactions_add` / `reactions_remove` use **`emoji`**, not `name` or `reaction`.
- `conversations_history` `limit` accepts **time-range strings** (`"1d"`, `"1w"`, `"30d"`) OR a number of messages (`"50"`). When `cursor` is provided, `limit` must be empty.
- `conversations_add_message` `content_type` defaults to `text/markdown` — use `text/plain` only when you want literal text without markdown rendering.
- `channel_id` accepts the raw ID (`C05JG6KUS1J`) OR a name prefix (`#general`, `@username_dm`). When the user gives a URL, extract the ID (see below).

## Parsing Slack URLs

Users often paste Slack URLs instead of giving a channel ID directly. Parse
them as follows — this is the single most common source of confusion.

### App URL: `https://app.slack.com/client/<TEAM_ID>/<CHANNEL_ID>`
- Example: `https://app.slack.com/client/T02FD6TBH3L/C05JG6KUS1J`
- Channel ID = `C05JG6KUS1J` (the segment after the team ID)
- No thread info in this URL format.

### Archives URL: `https://<workspace>.slack.com/archives/<CHANNEL_ID>/p<MSG_ID>`
- Example: `https://vnlabcenter.slack.com/archives/C05JG6KUS1J/p1782269365692859`
- Channel ID = `C05JG6KUS1J` (segment after `archives/`)
- Message/thread ts = **insert a dot before the last 6 digits** of the `p...` value:
  - `p1782269365692859` → `1782269365.692859`
  - `p1782103396720169` → `1782103396.720169`
- This ts can be used directly as `thread_ts` in `conversations_replies` or
  `conversations_add_message`, or as `timestamp` in `reactions_add`.

### Thread URL with query params
Some archive URLs include `?thread_ts=1782098365.328009&cid=C05JG6KUS1J`.
- `cid` param = channel ID
- `thread_ts` param = thread ts (already in the correct `dots` format)

**Always extract the channel ID and thread ts from URLs before calling tools**
rather than asking the user to provide them separately — they already gave you
the URL, so just parse it.

## Time-range mapping

When the user says things like "hôm nay", "hôm qua", "today", "yesterday",
"this week", map to the `limit` parameter of `conversations_history`:

| User phrase | `limit` value |
|-------------|---------------|
| "today" / "hôm nay" | `"1d"` |
| "yesterday" / "hôm qua" | `"2d"` (covers yesterday + today, then filter) |
| "this week" / "tuần này" | `"1w"` |
| "last 30 days" / "30 ngày qua" | `"30d"` |
| a specific number of messages | that number as a string, e.g. `"50"` |

If the user asks for a specific date range that doesn't map cleanly, use a
generous `limit` (e.g. `"7d"`) and then filter results by the `Time` field in
the returned CSV.

## Core workflows

### 1. Summarize a channel's discussion (for a day or range)

This is the most common request. Do it efficiently:

1. **Parse the channel reference** — URL, channel ID, or channel name → get `channel_id`.
2. **Fetch channel history** — call `conversations_history` with the right `limit`.
   - The response is a CSV-formatted text with columns: `MsgID,UserID,UserName,RealName,Channel,ThreadTs,Text,Time,Permalink,Reactions,BotName,FileCount,AttachmentIDs,HasMedia,Cursor`.
   - Each row is a message. The `ThreadTs` column tells you whether a message
     is a thread parent (when `ThreadTs` == `MsgID`) or a reply inside a thread
     (when `ThreadTs` != `MsgID`), or a standalone non-thread message.
   - The last row's `Cursor` column value is the pagination cursor — if non-empty, there are more messages.
3. **Identify thread parents** — messages where `ThreadTs == MsgID` (or where
   the user specifically asks about a thread). Collect their `MsgID` values —
   these are the `thread_ts` values you'll fetch replies for.
4. **Batch-fetch all thread replies in parallel** — issue all
   `conversations_replies` calls in a **single tool-call block** (one message,
   multiple `mcp_call_tool` invocations). This is critical for speed: fetching
   threads one-by-one is extremely slow. If there are 15 threads, make 15
   parallel calls in one turn.
5. **Handle truncation** — if any `conversations_replies` or
   `conversations_history` response is truncated, you'll see a
   `<truncation_notice>` tag with a file path. Read that file to get the full
   content. Don't silently drop truncated content.
6. **Synthesize** — group messages by thread, summarize each thread's topic and
   outcome, then present a structured summary. See "Summary output format" below.

### 2. Post / cross-post a message

1. **Determine the target channel** — from URL, channel ID, or name.
2. **Determine the content** — if the user asks to "post the summary to
   channel X", compose a well-structured markdown message (see format below).
3. **Call `conversations_add_message`** with `channel_id`, `text`, and
   `content_type: "text/markdown"` (default).
4. **If replying in a thread** — include `thread_ts` of the parent message.
5. **Confirm** — tell the user the channel and timestamp returned.

For cross-posting a summary to another channel: keep the full content in the
`text` parameter. If the message is very long (> 4000 chars), consider whether
it should be split — but Slack handles long markdown messages fine, so usually
one message is OK.

### 3. Add a reaction

1. **Identify the message** — from a URL (parse `p...` → ts) or the user tells
   you which message (e.g. "like Huy's message", "thả reaction cho tin nhắn
   của X"). When the user references a person by name, look through the thread
   replies or channel history you already fetched to find that person's
   `UserName` or `RealName` → get their message's `MsgID` → use as `timestamp`.
2. **Determine the emoji** — the user may say "like", "thumbs up", "+1",
   "heart", "love", "clap", or a specific emoji name. Map common phrases:
   - "like" / "thumbs up" / "👍" → `"thumbsup"` or `"+1"`
   - "love" / "heart" / "❤️" → `"heart"`
   - "clap" / "👏" → `"clap"`
   - "fire" / "🔥" → `"fire"`
   - "eyes" / "👀" → `"eyes"`
   - "tada" / "🎉" → `"tada"`
   - "check" / "✅" → `"white_check_mark"`
   - "ok" / "👌" → `"ok_hand"`
   - "pray" / "🙏" → `"pray"`
   - "100" / "💯" → `"100"`
   - "raised hands" / "🙌" → `"raised_hands"`
   - Japanese-specific: `"arigatou-gozaimasu"`, `"man-bowing"`,
     `"承知_しました"`, `"お疲れ様でした"`, `"お大事に-1"`
   - If the user types a Slack emoji code like `:thumbsup:` → strip colons →
     `"thumbsup"`. Custom emoji with hyphens/underscores keep them as-is.
3. **Call `reactions_add`** with `channel_id`, `timestamp`, and `emoji`.
   - **Critical**: the parameter is `emoji`, NOT `name` or `reaction`. This is
     the #1 parameter error with reactions — calling with `name` returns
     `"emoji is required"` error.
   - The `timestamp` parameter is the message's ts (same as `MsgID` in history
     responses, or the converted `p...` value from URLs).
4. **Confirm** — tell the user which message (by whom, what content snippet)
   got which reaction, so they can verify it was the right one.

**Edge case — reacting to a reply inside a thread (not the parent):**
The `timestamp` must be the **specific reply message's ts**, not the thread
parent's ts. When the user says "like Huy's reply", find Huy's message within
the thread replies and use its `MsgID` as `timestamp`, while keeping the
`channel_id` the same (the channel, not the thread).

### 4. Search / find specific content

The Slack MCP doesn't expose a search API directly. To find content across
channels or within a time range:

1. **Identify candidate channels** — use `channels_list` with a `query` if the
   user mentions a channel name, or `channels_me` for channels they've joined.
   If the user says "search all channels" or doesn't specify, use `channels_me`
   to get their joined channels, then fetch history from each (batch in parallel).
2. **Fetch history** with a generous `limit` (e.g. `"7d"` or `"30d"`).
   - Batch multiple `conversations_history` calls in parallel when searching
     across multiple channels.
3. **Scan the `Text` column** of the CSV for keywords the user mentioned.
   - Mentions like `<@U02E36L9LS0>` can be matched by UserID if the user
     mentions a person. Resolve UserID → UserName from other columns.
   - Keywords may be in Japanese, Vietnamese, or English — match case-insensitively
     and consider partial matches (e.g. "release" matches "リリース" context).
4. **Fetch thread replies** for any matching messages to get full context —
   batch these in parallel too.
5. **Present results** — list matching messages with channel, time, author,
   text snippet, and a link. Group by channel if searching multiple.

### 5. Reply in a thread

When the user wants to reply to a specific message or thread:

1. **Identify the thread** — from a URL (parse `p...` → thread_ts), or from a
   message the user references ("reply to takehiro's message about w/f").
2. **Determine the reply content** — the user may say "reply saying X" or
   "trả lời là Y" or just give you the content to post.
3. **Call `conversations_add_message`** with:
   - `channel_id`: the channel where the thread lives
   - `thread_ts`: the thread **parent's** ts (NOT the ts of the reply you're
     responding to — always the parent). If you have a reply's ts but not the
     parent's, the `ThreadTs` column from the history/replies CSV gives you
     the parent ts.
   - `text`: the reply content
   - `content_type`: `"text/markdown"` (default) for formatted replies
4. **Confirm** — tell the user the reply was posted and the message ts.

**Common confusion**: `thread_ts` must always be the **parent** message's ts,
even if you're replying to a reply deep in the thread. Slack threads are flat
under the parent — all replies go under the same parent ts.

### 6. Handle truncated output

When the Slack MCP returns a large response (long thread, many messages), the
output may be truncated. You'll see a `<truncation_notice>` tag like:
```
<truncation_notice>
Full output written to: /tmp/devin-overflows-1000/<hash>/content.txt
</truncation_notice>
```

**What to do:**
1. **Read the overflow file** immediately using the `read` tool — the path is
   in the `<truncation_notice>` tag. This file contains the full CSV/text.
   - Don't silently ignore truncated content — it may contain critical thread
     replies or the message you're looking for.
2. **Parse the full content** from the file, not the truncated inline text.
3. **If the overflow file itself is truncated** (very rare), use `cursor`
   pagination to fetch remaining messages in smaller batches.
4. **When fetching many threads**, some may truncate and some may not. Read
   each overflow file as needed — batch the `read` calls in parallel if
   multiple threads truncated.

**Prevention tips:**
- If you know a channel has very active threads, you can fetch threads in
  smaller batches (e.g. 5 at a time) to reduce truncation.
- Use `conversations_replies` with a `limit` parameter to cap the number of
  replies per thread if you only need recent replies.
- The `cursor` parameter in `conversations_replies` allows paginating through
  very long threads — pass the cursor from the last row to get older replies.

### 7. Check unread mentions (@ tags not yet read)

When the user asks "ai tag mình mà chưa đọc", "check mentions", "who @ me",
"xem ai TO @ mà chưa đọc":

1. **Determine the user's Slack UserID** — if not known, ask the user or look
   through recent messages they sent to find their UserID. Alternatively, the
   user may tell you their UserName, and you can find their UserID from the
   `UserID`/`UserName` columns in channel history.
2. **Identify channels to check** — use `channels_me` to list channels the
   user has joined. Focus on channels where the user is likely mentioned
   (work channels, not social ones, unless the user says otherwise).
3. **Fetch recent history** from each channel with `conversations_history`
   (batch in parallel). Use `"1d"` or `"2d"` for "today/yesterday" or `"1w"`
   for "this week".
4. **Scan the `Text` column** for mentions of the user's UserID in the format
   `<@UXXXXXXXXXX>`. The mention appears as the raw UserID, not the username.
   - Also check for `<!here>`, `<!channel>`, `<!subteam^...>` mentions which
     tag everyone in a channel/subteam — these may be relevant if the user
     is in that group.
5. **For each mention found**, check if it's in a thread (ThreadTs != empty
   and != MsgID means it's a reply; ThreadTs == MsgID means thread parent).
   Fetch thread replies for context if needed.
6. **Determine "unread" status** — the Slack MCP doesn't directly expose
   read/unread state. Heuristics:
   - If the user is asking "what haven't I read", they likely mean "what
     mentions exist that I might have missed". Present ALL recent mentions
     with timestamps and context, and let the user decide which they've seen.
   - Use `conversations_mark` with the channel_id and ts to mark messages as
     read after the user confirms they've seen them.
7. **Present results** — for each unread mention, show:
   - **Channel** (name or ID)
   - **Who mentioned** (UserName/RealName)
   - **Time**
   - **Message snippet** (the text around the mention)
   - **Thread context** (if it's in a thread, summarize what the thread is about)
   - **Link** (Permalink if available, or construct archives URL)

**Output format for unread mentions:**
```markdown
## Unread mentions for <user> — <date range>

### 1. <Channel> — <Author> @ <Time>
> <message snippet with the mention highlighted>

**Thread context**: <what the thread is about, if applicable>

### 2. ...

---
*<Total: N mentions across M channels>*
```

**Marking as read**: After presenting, offer to mark the channels as read using
`conversations_mark` — but only do this if the user confirms, as it's a
state-changing operation.

### 8. Check group mentions (@here, @channel, @subteam)

When the user asks "ai @here/@channel hôm nay", "group mentions", "who tagged
everyone", "xem ai @here @channel":

1. **Use `conversations_search_messages`** with these search queries (run in
   parallel in a single tool-call block):
   - `search_query: "<!here>"` — matches @here mentions
   - `search_query: "<!channel>"` — matches @channel mentions
   - `search_query: "<!subteam>"` — matches @subteam (user group) mentions
2. **Set date filter**:
   - `filter_date_during: "2026-06-24"` for "today"
   - `filter_date_after: "2026-06-20"` for "this week"
   - Use the actual date — convert "today"/"yesterday" to YYYY-MM-DD.
3. **Filter out bot messages** — exclude rows where:
   - `BotName` is non-empty (e.g. `Amazon Q Developer`, `miyao-bot`)
   - `UserID` is a known bot ID (e.g. `U03SFLMAT6E` for AWS, `USLACKBOT`)
   - `UserName` is `hunter`, `chị chị em em`, `wf_bot_*`, etc.
   Keep only human-sent group mentions, unless the user asks for bot alerts too.
4. **Parse and present** — for each human group mention, show:
   - **Time** (converted to JST or user's TZ if needed)
   - **Sender** (RealName or UserName)
   - **Channel** (channel name from the Channel column)
   - **Message snippet** (first 100-150 chars of Text)
   - **Mention type** (@here / @channel / @subteam)

**Output format for group mentions:**
```markdown
## Group mentions — <date>

### @here (N messages)
| Time | Sender | Channel | Message |
|------|--------|---------|---------|
| HH:MM | <name> | #<channel> | <snippet> |

### @channel (N messages)
| Time | Sender | Channel | Message |
|------|--------|---------|---------|
| HH:MM | <name> | #<channel> | <snippet> |

### @subteam (N messages)
| Time | Sender | Channel | Message |
|------|--------|---------|---------|
| HH:MM | <name> | #<channel> | <snippet> |

---
*Total: N human group mentions (bots excluded)*
```

**Tips:**
- `<!here>` notifies active members in the channel; `<!channel>` notifies ALL
  members; `<!subteam^S...>` notifies a specific user group.
- Bot channels (build notifications, AWS alerts) often use `<!channel>` —
  filter these out unless the user specifically wants them.
- The search query must include the angle brackets: `"<!here>"` not `"!here"`.
- If the user asks for both direct @mentions AND group mentions, combine
  workflow 7 (direct mentions) and workflow 8 (group mentions) in one response.

## Summary output format

When summarizing a channel's discussion, use this structure (adapt the
language to match the user's language — Vietnamese, Japanese, English, etc.):

```markdown
## Tóm tắt thảo luận channel <channel> — <date>

### 1. <Thread topic 1>
- <Who> said <what>
- <Key decisions / outcomes>
- <Links to PRs/issues if mentioned>

### 2. <Thread topic 2>
...

### N. Misc
- <Brief items: reminders, bot messages, attendance notices>

---
*<One-line overall summary of the day's themes>*
```

Group related threads together even if they appeared separately — e.g. if
three threads are all about "release 6/25", combine them under one heading.
Lead with the most important discussions. Keep each thread summary to 2-5
bullet points unless the user asks for detail.

## Efficiency rules

- **Always batch `conversations_replies` calls** in a single tool-call block
  when fetching multiple threads. This is the #1 speed win.
- **Batch `conversations_history` calls** in parallel when checking multiple
  channels (e.g. for unread mentions or cross-channel search).
- **Call `mcp_list_tools` once** at the start of a Slack-related session to
  confirm tool names, then trust the cheat sheet above for param names.
- **Don't ask the user for channel IDs** if they gave you a URL — parse it.
- **Don't re-fetch history** you already have in context.
- **Read truncation files** when responses are cut off — the full data matters.
  Batch `read` calls in parallel if multiple threads truncated.
- **When the user references a message by person name** (e.g. "like Huy's
  message"), look through the recent thread replies you already fetched to
  find that person's message and get its `MsgID` → use as `timestamp`.
- **For reactions, always use `emoji` parameter** — never `name` or `reaction`.
  This is the most common parameter error.
- **For thread replies, always use the parent message's ts as `thread_ts`** —
  not the ts of the specific reply you're responding to.
- **When checking unread mentions**, scan for `<@U...>` patterns in the Text
  column. The UserID in mentions is raw (e.g. `U02E36L9LS0`), not the username.

## Language matching

Match the user's language for all output. If the user writes in Vietnamese,
summarize in Vietnamese. If the channel content is in Japanese but the user
asks in Vietnamese, summarize in Vietnamese (translating the Japanese content).
If the user asks in English, use English. When posting messages to Slack,
use the language appropriate for that channel's audience (usually matching the
channel's primary language).
