#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it and run this launcher again." >&2
  exit 1
fi
python3 assemble_pak.py
python3 serve.py &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT INT TERM
url='http://127.0.0.1:8765/'
i=0
until python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8765/",timeout=1).read(16)' >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 20 ]; then echo 'The local server did not start; check whether port 8765 is busy.' >&2; exit 1; fi
  sleep 1
done
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then open "$url" || true
else echo "Open $url in a browser."
fi
wait "$server_pid"
