#!/bin/bash
set -e

PROJECT_ID=$1
REGION=${2:-us-central1}

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: ./deploy.sh <project-id> [region]"
  echo "Example: ./deploy.sh my-red-team-project us-central1"
  exit 1
fi

echo "🚀 Starting deployment for project: $PROJECT_ID"

# Set default project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  workflows.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  firebase.googleapis.com

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker

# Build and push agent containers
echo "🏗 Building and pushing agent containers..."
./scripts/build-agents.sh $PROJECT_ID

# Deploy infrastructure with Terraform
echo "🏗 Deploying infrastructure with Terraform..."
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION"
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve
cd ..

# Deploy Cloud Workflow
echo "📋 Deploying Cloud Workflow..."
gcloud workflows deploy red-team-attack-chain \
  --source=workflows/attack-chain.yaml \
  --location=$REGION

# Deploy Dashboard
echo "🎨 Deploying Dashboard..."
cd dashboard
npm install
npm run build

# Initialize Firebase (if not already done)
firebase login --no-localhost
firebase use $PROJECT_ID
firebase deploy --only hosting
cd ..

echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Dashboard URL: https://${PROJECT_ID}.web.app"
echo "🔧 Next steps:"
echo "  1. Configure authentication in Firebase Console"
echo "  2. Set up billing alerts in GCP Console"
echo "  3. Review security settings and IAM permissions"
echo "  4. Test the system with authorized targets only"
echo ""
echo "⚠️  IMPORTANT: Only use this system against authorized targets!"
