"""
lane_kda.py — Compute the KDA for a specific lane across a player's recent
matches, using the official Riot Games API.

Note: the KDA is calculated for whoever played the requested lane on the
given player's TEAM in each match — not necessarily the given player's own
stats. For example, running this with --lane BOTTOM for a player who always
plays TOP will report the KDA of their team's ADC in those matches.

Setup:
    pip install requests

    Get a Riot API key from https://developer.riotgames.com/
    (log in, generate a "Development API Key" — note it expires every 24h).

Usage:
    python lane_kda.py --api-key RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \\
        --name "Faker" --tag "KR1" --region asia --lane MIDDLE --count 20

Arguments:
    --api-key   Riot API key (required)
    --name      Riot ID game name, e.g. "Faker" (required)
    --tag       Riot ID tagline, e.g. "KR1" (required)
    --region    Routing continent: americas, asia, or europe (default: asia)
    --lane      TOP, JUNGLE, MIDDLE, BOTTOM, or UTILITY — the lane whose
                KDA is computed, on the given player's team (required)
    --count     Number of recent matches to scan (default: 20)
"""

import argparse
import sys
import time

import requests

VALID_LANES = {"TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"}
VALID_REGIONS = {"americas", "asia", "europe"}
REQUEST_DELAY_SECONDS = 1.2


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate a League of Legends player's KDA for a specific lane."
    )
    parser.add_argument("--api-key", required=True, help="Riot API key")
    parser.add_argument("--name", required=True, help="Riot ID game name")
    parser.add_argument("--tag", required=True, help="Riot ID tagline")
    parser.add_argument(
        "--region",
        default="asia",
        choices=sorted(VALID_REGIONS),
        help="Routing continent: americas, asia, or europe (default: asia)",
    )
    parser.add_argument(
        "--lane",
        required=True,
        help="Lane to filter on: TOP, JUNGLE, MIDDLE, BOTTOM, or UTILITY",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of recent matches to scan (default: 20)",
    )
    return parser.parse_args()


def riot_get(url, api_key, params=None):
    try:
        response = requests.get(
            url, headers={"X-Riot-Token": api_key}, params=params, timeout=10
        )
    except requests.exceptions.RequestException as exc:
        print(f"Error: network request failed for {url}: {exc}", file=sys.stderr)
        sys.exit(1)

    if response.status_code == 401:
        print("Error: 401 Unauthorized — check that your API key is valid.", file=sys.stderr)
        sys.exit(1)
    if response.status_code == 403:
        print(
            "Error: 403 Forbidden — your API key may have expired or lacks access.",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 429:
        print(
            "Error: 429 Too Many Requests — you hit Riot's rate limit. "
            "Wait a bit and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    if response.status_code == 404:
        print(f"Error: 404 Not Found for {url}", file=sys.stderr)
        sys.exit(1)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        print(f"Error: HTTP {response.status_code} for {url}: {exc}", file=sys.stderr)
        sys.exit(1)

    return response.json()


def get_puuid(region, game_name, tag_line, api_key):
    url = (
        f"https://{region}.api.riotgames.com/riot/account/v1/accounts/"
        f"by-riot-id/{game_name}/{tag_line}"
    )
    data = riot_get(url, api_key)
    return data["puuid"]


def get_match_ids(region, puuid, count, api_key):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {"start": 0, "count": count}
    return riot_get(url, api_key, params=params)


def get_match_detail(region, match_id, api_key):
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    return riot_get(url, api_key)


def main():
    args = parse_args()

    lane = args.lane.upper()
    if lane not in VALID_LANES:
        print(
            f"Error: invalid --lane '{args.lane}'. Must be one of: "
            f"{', '.join(sorted(VALID_LANES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    puuid = get_puuid(args.region, args.name, args.tag, args.api_key)
    match_ids = get_match_ids(args.region, puuid, args.count, args.api_key)

    if not match_ids:
        print("No matches found for this player.")
        sys.exit(0)

    total_kills = 0
    total_deaths = 0
    total_assists = 0
    games_counted = 0

    for i, match_id in enumerate(match_ids):
        match = get_match_detail(args.region, match_id, args.api_key)

        participants = match.get("info", {}).get("participants", [])
        me = next((p for p in participants if p.get("puuid") == puuid), None)

        if me is not None:
            lane_player = next(
                (
                    p
                    for p in participants
                    if p.get("teamId") == me.get("teamId")
                    and p.get("teamPosition") == lane
                ),
                None,
            )
            if lane_player is not None:
                total_kills += lane_player.get("kills", 0)
                total_deaths += lane_player.get("deaths", 0)
                total_assists += lane_player.get("assists", 0)
                games_counted += 1

        if i < len(match_ids) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    if games_counted == 0:
        print(
            f"No games found with a '{lane}' player on {args.name}'s team, "
            f"out of {len(match_ids)} matches scanned."
        )
        sys.exit(0)

    print(f"Kills: {total_kills}")
    print(f"Deaths: {total_deaths}")


if __name__ == "__main__":
    main()
