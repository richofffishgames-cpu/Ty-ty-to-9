# Quick Deploy - Red Team Agent Swarm

## One-Command Deployment

If you have all prerequisites installed, simply run:

```bash
cd red-team-swarm
chmod +x quick-deploy.sh
./quick-deploy.sh YOUR_PROJECT_ID us-central1
```

## Manual Step-by-Step Deployment

### Step 1: Prerequisites Check
```bash
# Verify tools are installed
gcloud --version
terraform --version
docker --version
firebase --version
node --version
```

### Step 2: Authenticate
```bash
# Login to Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 3: Run Full Deployment
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Option A: Use the main deploy script
./scripts/deploy.sh YOUR_PROJECT_ID us-central1

# Option B: Or run quick-deploy for automated deployment
./quick-deploy.sh YOUR_PROJECT_ID us-central1
```

### Step 4: Access Your Dashboard

After deployment completes, access your dashboard at:
```
https://YOUR_PROJECT_ID.web.app
```

## Post-Deployment Setup

### 1. Configure Firebase Authentication
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Authentication** → **Sign-in method**
4. Enable **Email/Password** or **Google** sign-in
5. Add authorized users

### 2. Update Firestore Security Rules
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

### 3. Set Billing Alerts
1. Go to [GCP Billing](https://console.cloud.google.com/billing)
2. Create budget with alerts at 50%, 80%, 100%

## Verify Deployment

```bash
# Check services
gcloud run services list
gcloud pubsub topics list
gcloud workflows list

# View logs
gcloud logging read "resource.labels.service_name=recon-agent" --limit=10
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | Run: `gcloud auth login` |
| Docker push fails | Run: `gcloud auth configure-docker` |
| Terraform fails | Check APIs: `gcloud services list --enabled` |
| Dashboard 404 | Rebuild: `cd dashboard && npm run build && firebase deploy` |

## Cleanup

To destroy everything:
```bash
./scripts/cleanup.sh YOUR_PROJECT_ID
```

---

**⚠️ Only deploy against systems you own or have explicit written permission to test!**
