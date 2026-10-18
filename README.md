# Second brain: install runbook for Claude Code

This repository is written for you, Claude Code, running on the person's own computer. The person asked you to
carry it out from start to finish. Do every step yourself; the person only answers what you ask them. Their second
brain will remember everything they do with Claude Code and bring it back when it helps.

## Rules for the whole run

- Talk to the person in Dutch, unless they write to you in another language. Keep every message to one or two short
  sentences: what is happening now, or the one thing you need from them. No explanations of how it works.
- Only run the commands in this file. Do not edit files, settings or scripts yourself; the script does that.
- Never print, repeat, log or put in a command line a token, password or API key. When one is needed, the person
  types it into Terminal themselves (step 4).
- When the script prints a line starting with `MISLUKT`, tell the person that line, add "Valentine is op de hoogte
  gebracht" only if the line says so, and stop.
- Pass on the script's own Dutch lines to the person as they are; they are written for them.

## Step 1: check the computer

Run `uname`. If it does not print `Darwin`, tell the person: "Deze installatie werkt nu alleen op een Mac. Windows
komt binnenkort." and stop.

## Step 2: download the script

```bash
curl -fsSL https://raw.githubusercontent.com/madebyvalentine/second-brain-install/main/install.sh -o ~/.second-brain-install.sh
```

## Step 3: send the request

```bash
bash ~/.second-brain-install.sh start
```

- Exit code 0: the request is sent. Tell the person the line it printed and go to step 4.
- Exit code 3 with `NEED name`: ask the person for their full name, then run
  `bash ~/.second-brain-install.sh start --name "<name>"`.
- Exit code 3 with `NEED email`: ask for their email address, then run it again with `--email <address>` (and
  `--name` if you asked for that too).
- It prints `Er loopt al een aanvraag`: go straight to step 4.

## Step 4: wait for Valentine

```bash
bash ~/.second-brain-install.sh wait
```

Run this with a timeout of 10 minutes (600000 ms). Valentine approves every request himself, so this can take minutes
or hours. Each time it ends without a final answer, run it again, and keep doing that until one of these:

- It prints `staat klaar`: the brain is installed. Go to step 5.
- It prints `niet goedgekeurd`: tell the person and stop.
- Exit code 1: tell the person the line and stop.
- Exit code 4 with `NEED api_key`: tell the person: "Valentine heeft gekozen voor je eigen API-key. Open Terminal,
  plak dit commando en daarna je Anthropic API-key, en druk op Enter:" and give them
  `bash ~/.second-brain-install.sh token`. When they say it is done, run step 4 again.
- Exit code 4 with `NEED setup_token`: tell the person: "Valentine heeft gekozen voor je eigen Claude-abonnement.
  Open Terminal en voer `claude setup-token` uit. Klik in de browser op Authorize. Kopieer het token dat Terminal
  daarna laat zien, voer `bash ~/.second-brain-install.sh token` uit, plak het token en druk op Enter." When they
  say it is done, run step 4 again.

While you wait, tell the person once: "Je aanvraag ligt bij Valentine. Ik wacht tot hij hem goedkeurt." Do not repeat
it after every round.

## Step 5: done

Tell the person: "Je second brain is klaar. Start een nieuwe sessie in Claude Code; vanaf dan onthoudt het wat je
doet." Then stop. You are finished.

## Reference

- `install.sh status` prints where the request stands.
- Exit codes: 0 done, 1 failed (the printed line says why), 3 needs a name or email, 4 needs the person's token.
- What the script changes: `~/.second-brain/` (the brain's address, a small client and, when the Mac has none, a
  Python of its own), five hooks in `~/.claude/settings.json` (merged; a copy of the old file is kept as
  `settings.json.before-brain`), the `second-brain` MCP server at user level, a short block in `~/.claude/CLAUDE.md`,
  and the brain's key in the macOS Keychain.
