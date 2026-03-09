#!/bin/bash
# Quick Deploy Script for Red Team Agent Swarm
# Usage: ./quick-deploy.sh <project-id> [region]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project ID
PROJECT_ID=$1
REGION=${2:-us-central1}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Project ID is required${NC}"
    echo "Usage: ./quick-deploy.sh <project-id> [region]"
    echo "Example: ./quick-deploy.sh my-project-id us-central1"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Red Team Agent Swarm - Quick Deployment               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud is required but not installed.${NC}"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}terraform is required but not installed.${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}docker is required but not installed.${NC}"; exit 1; }
command -v firebase >/dev/null 2>&1 || { echo -e "${RED}firebase is required but not installed.${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}npm is required but not installed.${NC}"; exit 1; }

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Verify gcloud authentication
echo -e "${YELLOW}Verifying GCP authentication...${NC}"
ACCOUNT=$(gcloud config get-value account 2>/dev/null)
if [ -z "$ACCOUNT" ]; then
    echo -e "${RED}Not authenticated. Running gcloud auth login...${NC}"
    gcloud auth login
fi
echo -e "${GREEN}✓ Authenticated as: $ACCOUNT${NC}"
echo ""

# Set project
echo -e "${YELLOW}Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID
echo -e "${GREEN}✓ Project set${NC}"
echo ""

# Enable APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    pubsub.googleapis.com \
    workflows.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com \
    iam.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    firebase.googleapis.com \
    --quiet
echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Configure Docker
echo -e "${YELLOW}Configuring Docker for Google Container Registry...${NC}"
gcloud auth configure-docker --quiet
echo -e "${GREEN}✓ Docker configured${NC}"
echo ""

# Build agents
echo -e "${YELLOW}Building and pushing agent containers...${NC}"
for AGENT in recon validation amplifier; do
    echo -e "${BLUE}  Building $AGENT agent...${NC}"
    cd agents/$AGENT
    docker build -t gcr.io/$PROJECT_ID/$AGENT-agent:latest . >/dev/null 2>&1
    docker push gcr.io/$PROJECT_ID/$AGENT-agent:latest >/dev/null 2>&1
    cd ../..
    echo -e "${GREEN}  ✓ $AGENT agent built and pushed${NC}"
done
echo ""

# Terraform deployment
echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"
cd terraform
terraform init -input=false
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION" -input=false -out=tfplan
terraform apply -input=false tfplan
cd ..
echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo ""

# Deploy workflow
echo -e "${YELLOW}Deploying Cloud Workflow...${NC}"
gcloud workflows deploy red-team-attack-chain \
    --source=workflows/attack-chain.yaml \
    --location=$REGION \
    --quiet
echo -e "${GREEN}✓ Workflow deployed${NC}"
echo ""

# Deploy dashboard
echo -e "${YELLOW}Building and deploying dashboard...${NC}"
cd dashboard
npm install --silent
npm run build --silent

# Check if Firebase is initialized
if [ ! -f .firebaserc ]; then
    echo -e "${YELLOW}  Initializing Firebase...${NC}"
    firebase use $PROJECT_ID --add --alias default
fi

firebase deploy --only hosting --quiet
cd ..
echo -e "${GREEN}✓ Dashboard deployed${NC}"
echo ""

# Get outputs
echo -e "${YELLOW}Getting deployment outputs...${NC}"
cd terraform
DASHBOARD_URL=$(terraform output -raw firebase_config 2>/dev/null | grep -o '"authDomain": "[^"]*"' | cut -d'"' -f4 || echo "")
cd ..

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Deployment Complete!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Dashboard URL:${NC} https://$PROJECT_ID.web.app"
echo ""
echo -e "${BLUE}Cloud Run Services:${NC}"
gcloud run services list --format="table(metadata.name, status.conditions[0].status)"
echo ""
echo -e "${BLUE}Pub/Sub Topics:${NC}"
gcloud pubsub topics list --format="value(name)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Configure Firebase Authentication in the console"
echo "  2. Set up billing alerts in GCP Console"
echo "  3. Review IAM permissions"
echo "  4. Test with authorized targets only!"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Only use this system against authorized targets!${NC}"
