#!/bin/bash

echo "=== Checking Zitadel Setup ==="
echo

echo "1. Current directory:"
pwd
echo

echo "2. Files in directory:"
ls -la
echo

echo "3. Docker Compose version:"
docker-compose version
echo

echo "4. Current containers:"
docker-compose ps
echo

echo "5. Zitadel container logs (last 30 lines):"
docker-compose logs --tail=30 zitadel
echo

echo "6. Checking for any docker-compose override files:"
ls -la docker-compose*.yml
echo

echo "7. Checking environment variables:"
env | grep -i compose
echo

echo "8. Inspecting the actual command being run:"
CONTAINER_ID=$(docker-compose ps -q zitadel)
if [ ! -z "$CONTAINER_ID" ]; then
    echo "Container ID: $CONTAINER_ID"
    docker inspect $CONTAINER_ID | grep -A 10 '"Cmd"'
    echo
    echo "Full command:"
    docker inspect $CONTAINER_ID --format='{{join .Config.Cmd " "}}'
else
    echo "No running zitadel container found"
fi
echo

echo "9. Checking docker-compose config:"
docker-compose config | grep -A 5 "command:"