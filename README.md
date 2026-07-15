# lol_kda_count

A small command-line tool that uses the official Riot Games API to total up
kills and deaths for a specific lane, across a player's recent matches.

**Note:** the tallied stats belong to whoever played the requested lane on
the given player's **team** in each match — not necessarily the given
player's own stats. For example, running this with `--lane BOTTOM` for a
player who always plays TOP will report their team's ADC numbers in those
matches.

## Setup

1. Install the one dependency:

   ```bash
   pip install requests
   ```

2. Get a Riot API key from [developer.riotgames.com](https://developer.riotgames.com/):
   log in, and generate a **Development API Key** from your dashboard.

   > Development keys expire every 24 hours — you'll need to regenerate one
   > each time it goes stale (you'll see `401 Unauthorized` errors when it has).

## Usage

```bash
python lane_kda.py \
  --api-key RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
  --name "Faker" \
  --tag "KR1" \
  --region asia \
  --lane MIDDLE \
  --count 20
```

Run it as a single line — pasting a multi-line command with `\` continuations
can silently break in some terminals if the line breaks don't survive the paste.

### Arguments

| Flag         | Required | Default | Description                                                                 |
|--------------|----------|---------|------------------------------------------------------------------------------|
| `--api-key`  | yes      | —       | Riot API key                                                                  |
| `--name`     | yes      | —       | Riot ID game name (the part before the `#`)                                   |
| `--tag`      | yes      | —       | Riot ID tagline (the part after the `#`, e.g. `KR1`, `EUW`, or a custom tag)   |
| `--region`   | no       | `asia`  | Routing continent: `americas`, `asia`, or `europe`                            |
| `--lane`     | yes      | —       | `TOP`, `JUNGLE`, `MIDDLE`, `BOTTOM`, or `UTILITY`                              |
| `--count`    | no       | `20`    | Number of recent matches to scan                                              |

`--region` is the **routing continent**, not the platform shard — use
`europe` for EUW/EUNE/TR/RU accounts, `americas` for NA/BR/LAN/LAS/OCE, and
`asia` for KR/JP.

Finding your Riot ID's tag: open the League client and look at the top-right
corner near your name — it's displayed as `Name#TAG`.

### Output

```
Kills: 148
Deaths: 127
```

If no games in the requested lane are found within the scanned matches, or
zero matches exist for the player, the script prints a message explaining
that and exits cleanly instead of erroring.

## How it works

1. Looks up the player's PUUID via the Account-V1 endpoint.
2. Fetches their `--count` most recent match IDs via Match-V5.
3. Fetches full match details for each match ID (with a ~1.2s delay between
   requests to respect Riot's per-second rate limit on development keys).
4. For each match, finds the player's team, then finds whichever participant
   on that team has `teamPosition` matching `--lane`, and adds their
   kills/deaths to the running totals.

## Local development

`run_bottom.sh` is a convenience wrapper that runs the script with a fixed
set of arguments. It reads `RIOT_API_KEY` from a local `.env` file (not
committed — see `.gitignore`), so create one like this before running it:

```
RIOT_API_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Then:

```bash
bash run_bottom.sh
```
