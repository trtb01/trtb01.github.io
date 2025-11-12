#!/bin/bash

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <file> [port]"
    exit 1
fi

FILE="$1"
PORT="${2:-1222}"

if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

CONTENT_TYPE="application/octet-stream"

# Set content type based on file extension
case "${FILE##*.}" in
    html|htm) CONTENT_TYPE="text/html" ;;
    txt) CONTENT_TYPE="text/plain" ;;
    css) CONTENT_TYPE="text/css" ;;
    js) CONTENT_TYPE="application/javascript" ;;
    json) CONTENT_TYPE="application/json" ;;
    png) CONTENT_TYPE="image/png" ;;
    jpg|jpeg) CONTENT_TYPE="image/jpeg" ;;
    gif) CONTENT_TYPE="image/gif" ;;
esac

# Calculate file size
FILESIZE=$(stat -c%s "$FILE")

echo "Serving $FILE on port $PORT"
while true; do
    {
        echo -ne "HTTP/1.1 200 OK\r\n"
        echo -ne "Content-Type: $CONTENT_TYPE\r\n"
        echo -ne "Content-Length: $FILESIZE\r\n"
        echo -ne "Connection: close\r\n"
        echo -ne "\r\n"
        cat "$FILE"
    } | nc -l -p $PORT
done
