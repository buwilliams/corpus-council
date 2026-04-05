#!/usr/bin/env bash
set -e

# Kill any existing servers
pgrep -f "corpus_council" | xargs -r kill 2>/dev/null || true
sleep 2

# Start server
uv run corpus-council serve &
APP_PID=$!
echo "Started server PID=$APP_PID"

# Wait for server to be ready
for i in $(seq 1 20); do
  curl -sf http://localhost:8000/docs > /dev/null 2>&1 && echo "Server up at attempt $i" && break
  sleep 1
  if [ $i -eq 20 ]; then
    kill $APP_PID
    echo "TIMEOUT waiting for server"
    exit 1
  fi
done

curl -sf http://localhost:8000/docs > /dev/null

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/conversation \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user0001","message":"test"}')
echo "Conversation status: $STATUS"
if [[ ! "$STATUS" =~ ^(200|500|422)$ ]]; then
  kill $APP_PID
  echo "FAIL: unexpected conversation status $STATUS"
  exit 1
fi

STATUS2=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/collection/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user0001","plan_id":"test"}')
echo "Collection start status: $STATUS2"
if [[ ! "$STATUS2" =~ ^(201|404|500|422)$ ]]; then
  kill $APP_PID
  echo "FAIL: unexpected collection/start status $STATUS2"
  exit 1
fi

kill $APP_PID
echo "server OK"
