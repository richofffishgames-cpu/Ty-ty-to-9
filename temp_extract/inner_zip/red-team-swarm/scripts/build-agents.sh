#!/bin/bash
set -e

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./build-agents.sh <project-id>"
  exit 1
fi

echo "🏗 Building agent containers for project: $PROJECT_ID"

# Build and push each agent
for AGENT in recon validation amplifier; do
  echo "Building $AGENT agent..."
  cd agents/$AGENT

  # Build the container
  docker build -t gcr.io/$PROJECT_ID/$AGENT-agent:latest .

  # Push to Google Container Registry
  docker push gcr.io/$PROJECT_ID/$AGENT-agent:latest

  echo "✅ $AGENT agent built and pushed successfully"
  cd ../..
done

echo "✅ All agent containers built and pushed successfully!"
