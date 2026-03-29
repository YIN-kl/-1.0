#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
USERNAME="${USERNAME:-admin}"
PASSWORD="${PASSWORD:-admin123}"

echo "Logging in as ${USERNAME} ..."

TOKEN=$(curl -sS -X POST "${BASE_URL}/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" | \
  python -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

echo "Asking a sample question ..."

curl -sS -X POST "${BASE_URL}/question" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{"input":"公司的考勤制度是什么？","detailed":false}'

echo
