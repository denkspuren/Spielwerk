#!/usr/bin/env sh
cd "$(dirname "$0")" || exit 1
exec python3 server.py games/space_invaders/SpaceInvaders.java "$@"
