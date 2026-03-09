# Red Team Agent Swarm - Deployment Guide

This guide walks you through deploying the Red Team Agent Swarm to Google Cloud Platform.

## ⚠️ Prerequisites

Before starting, ensure you have:

1. **Google Cloud Account** with billing enabled
2. **GCP Project** created (note the Project ID)
3. **Required tools installed:**
   - [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
   - [Terraform >= 1.0](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
   - [Docker](https://docs.docker.com/get-docker/)
   - [Node.js >= 16](https://nodejs.org/)
   - [Firebase CLI](https://firebase.google.com/docs/cli)

## Step 1: Authenticate with GCP

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify authentication
gcloud auth list
```

## Step 2: Enable Required APIs

```bash
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
```

## Step 3: Configure Docker for GCR

```bash
# Configure Docker to use Google Container Registry
gcloud auth configure-docker
```

## Step 4: Build and Push Agent Containers

```bash
cd red-team-swarm

# Make scripts executable
chmod +x scripts/*.sh

# Build all agent containers
./scripts/build-agents.sh YOUR_PROJECT_ID
```

This will build and push:
- `gcr.io/YOUR_PROJECT_ID/recon-agent:latest`
- `gcr.io/YOUR_PROJECT_ID/validation-agent:latest`
- `gcr.io/YOUR_PROJECT_ID/amplifier-agent:latest`

## Step 5: Deploy Infrastructure with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var="project_id=YOUR_PROJECT_ID" -var="region=us-central1"

# Apply the deployment
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="region=us-central1"

# Note the outputs - you'll need the Firebase config for the dashboard
cd ..
```

## Step 6: Deploy Cloud Workflow

```bash
# Deploy the attack chain workflow
gcloud workflows deploy red-team-attack-chain \
  --source=workflows/attack-chain.yaml \
  --location=us-central1
```

## Step 7: Deploy Dashboard

```bash
cd dashboard

# Install dependencies
npm install

# Update Firebase config with your project details
# Edit src/firebase-config.js with values from Terraform output

# Build the React app
npm run build

# Login to Firebase
firebase login

# Initialize Firebase (first time only)
firebase init hosting

# Select your project when prompted

# Deploy to Firebase Hosting
firebase deploy --only hosting

cd ..
```

## Step 8: Update Dashboard Firebase Config

After Terraform deployment, update `dashboard/src/firebase-config.js`:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",           // From Terraform output
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

Then rebuild and redeploy:
```bash
cd dashboard
npm run build
firebase deploy --only hosting
cd ..
```

## Step 9: Verify Deployment

### Check Cloud Run Services
```bash
gcloud run services list
```

You should see:
- recon-agent
- validation-agent
- amplifier-agent

### Check Pub/Sub Topics
```bash
gcloud pubsub topics list
```

You should see:
- recon-hypotheses
- validated-targets
- foothold-achieved
- human-decision-point

### Check Firestore Database
```bash
gcloud firestore databases list
```

### Access Dashboard
```
https://YOUR_PROJECT_ID.web.app
```

## Step 10: Test the System

### Start a Test Engagement

1. Open the dashboard at `https://YOUR_PROJECT_ID.web.app`
2. Click "Start Engagement"
3. Enter a test target (your own authorized system)
4. Select scan type
5. Click "Start Engagement"

### Monitor Progress

View real-time logs:
```bash
# Recon agent logs
gcloud logging read "resource.labels.service_name=recon-agent" --limit=20

# Validation agent logs
gcloud logging read "resource.labels.service_name=validation-agent" --limit=20

# Amplifier agent logs
gcloud logging read "resource.labels.service_name=amplifier-agent" --limit=20
```

View workflow executions:
```bash
gcloud workflows executions list --workflow=red-team-attack-chain
```

## Troubleshooting

### Issue: Permission Denied
```bash
# Grant yourself necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/owner"
```

### Issue: Container Push Fails
```bash
# Reconfigure Docker authentication
gcloud auth configure-docker
docker logout gcr.io
```

### Issue: Terraform Apply Fails
```bash
# Check if APIs are enabled
gcloud services list --enabled

# Re-enable if needed
gcloud services enable run.googleapis.com pubsub.googleapis.com ...
```

### Issue: Dashboard Not Loading
```bash
# Check Firebase hosting
cd dashboard
firebase hosting:channel:list

# Redeploy
npm run build
firebase deploy --only hosting
```

## Security Configuration

### 1. Set Up Authentication (Required)

In Firebase Console:
1. Go to Authentication → Sign-in method
2. Enable Email/Password or Google sign-in
3. Add authorized users

### 2. Configure Firestore Security Rules

In Firebase Console:
1. Go to Firestore Database → Rules
2. Update rules to restrict access:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 3. Set Up Billing Alerts

In GCP Console:
1. Go to Billing → Budgets & alerts
2. Create budget with alerts at 50%, 80%, 100%

### 4. Enable Audit Logging

```bash
gcloud logging sinks create red-team-audit \
  bigquery.googleapis.com/projects/YOUR_PROJECT_ID/datasets/red_team_logs \
  --log-filter='protoPayload.serviceName="run.googleapis.com"'
```

## Cost Estimation

| Resource | Estimated Monthly Cost (Light Usage) |
|----------|--------------------------------------|
| Cloud Run | $0-10 (pay per use) |
| Pub/Sub | $0-5 |
| Firestore | $0-5 |
| Cloud Storage | $0-2 |
| Firebase Hosting | $0 (free tier) |
| **Total** | **~$0-25/month** |

## Cleanup

To destroy all resources:

```bash
./scripts/cleanup.sh YOUR_PROJECT_ID
```

This will:
- Stop active workflows
- Destroy Terraform infrastructure
- Delete container images
- Disable Firebase hosting

## Next Steps

1. **Configure Authentication**: Set up Firebase Authentication
2. **Add SSL/TLS**: Enable HTTPS for all services
3. **Set Up Monitoring**: Configure Cloud Monitoring alerts
4. **Create Playbooks**: Document incident response procedures
5. **Regular Audits**: Review logs and access patterns

## Support

For deployment issues:
1. Check [GCP Documentation](https://cloud.google.com/docs)
2. Review [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
3. Check [Firebase Documentation](https://firebase.google.com/docs)

---

**⚠️ Remember**: Only use this system against authorized targets with proper legal documentation!
