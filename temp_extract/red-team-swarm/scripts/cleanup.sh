#!/bin/bash
set -e

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./cleanup.sh <project-id>"
  exit 1
fi

echo "🧹 Cleaning up Red Team Swarm resources..."

# Confirm destructive action
read -p "This will destroy all resources in project $PROJECT_ID. Are you sure? (yes/no): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
  echo "Cleanup cancelled."
  exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Stop any running workflows
echo "🛑 Stopping active workflows..."
gcloud workflows executions list --location=us-central1 --workflow=red-team-attack-chain --filter="state:ACTIVE" --format="value(name)" | while read -r execution; do
  gcloud workflows executions cancel $execution --location=us-central1 --workflow=red-team-attack-chain
done

# Destroy Terraform infrastructure
echo "🏗 Destroying infrastructure..."
cd terraform
terraform destroy -var="project_id=$PROJECT_ID" -auto-approve
cd ..

# Clean up container images
echo "🗑 Cleaning up container images..."
for AGENT in recon validation amplifier; do
  gcloud container images delete gcr.io/$PROJECT_ID/$AGENT-agent:latest --quiet --force-delete-tags || true
done

# Clean up Firebase hosting
echo "🔥 Cleaning up Firebase resources..."
cd dashboard
firebase hosting:disable --project=$PROJECT_ID || true
cd ..

echo "✅ Cleanup completed!"
echo "💡 You may want to manually verify that all resources have been removed in the GCP Console."
