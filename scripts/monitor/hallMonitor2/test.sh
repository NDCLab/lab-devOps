#!/bin/bash

FILENAME=reports/"test-$(date '+%Y%m%d_%H%M%S').html"

poetry run pytest --html="$FILENAME" || exit 1
echo "Tests complete!"

# Get absolute file path and URL
ABS_PATH=$(realpath "$FILENAME")
FILE_URL="file://$ABS_PATH"

# Try to open in browser
echo "Opening report in browser..."

if command -v xdg-open >/dev/null; then
  xdg-open "$FILE_URL"
elif command -v open >/dev/null; then
  open "$FILE_URL"
elif command -v start >/dev/null; then
  start "$FILE_URL"
else
  echo "Could not detect how to open the report in a browser."
fi
