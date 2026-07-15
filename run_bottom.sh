#!/bin/bash
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

: "${RIOT_API_KEY:?Set RIOT_API_KEY in a local .env file or export it before running}"

python3 lane_kda.py --api-key "$RIOT_API_KEY" --name "quante" --tag "urgot" --region americas --lane BOTTOM --count 20
