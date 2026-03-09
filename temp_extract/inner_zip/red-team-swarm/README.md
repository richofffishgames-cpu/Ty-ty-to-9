# Cloud-Native Red Team Agent Swarm

A sophisticated, serverless red team automation platform built on Google Cloud Platform. This system orchestrates autonomous security testing agents that can scale dynamically based on engagement requirements.

## ⚠️ CRITICAL DISCLAIMER

**This system is designed exclusively for authorized penetration testing and security research. You must have explicit written permission before deploying this against any systems. Unauthorized use may violate local, national, and international laws.**

## Architecture Overview

The system uses a serverless, event-driven architecture where:

- **Agent Core**: Containerized microservices on Cloud Run
- **Communication**: Asynchronous messaging via Cloud Pub/Sub
- **Orchestration**: Complex workflows managed by Cloud Workflows
- **Data Layer**: Real-time logging in Cloud Firestore
- **Storage**: Artifacts stored in Cloud Storage
- **Interface**: React-based dashboard with real-time updates

```
┌─────────────────────────────────────────────────────────────────┐
│                     Red Team Agent Swarm                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Recon Agent │───▶│Validation Agent│───▶│Amplifier Agent│     │
│  │  (Cloud Run) │    │  (Cloud Run)   │    │  (Cloud Run)  │     │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Cloud Pub/Sub (Message Bus)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Cloud Workflows (Orchestrator)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Cloud Firestore (Codex)  │  Cloud Storage (Artifacts)   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React Dashboard (Firebase Hosting)           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
red-team-swarm/
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # Main Terraform resources
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Output values
│   └── provider.tf        # Provider configuration
├── agents/                 # Agent implementations
│   ├── recon/             # Reconnaissance agent
│   ├── validation/        # Validation agent
│   └── amplifier/         # Exploitation agent
├── workflows/              # Cloud Workflows
│   └── attack-chain.yaml  # Main orchestration workflow
├── dashboard/              # React web interface
│   ├── public/
│   ├── src/
│   └── package.json
├── scripts/                # Deployment scripts
│   ├── deploy.sh          # Main deployment script
│   ├── build-agents.sh    # Build agent containers
│   └── cleanup.sh         # Cleanup resources
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Google Cloud account with billing enabled
- Terraform >= 1.0
- Docker
- Node.js >= 16
- Firebase CLI
- gcloud CLI

### Installation

1. **Clone and setup:**
```bash
git clone <this-repo>
cd red-team-swarm
chmod +x scripts/*.sh
```

2. **Deploy infrastructure:**
```bash
./scripts/deploy.sh YOUR_PROJECT_ID us-central1
```

3. **Access dashboard:**
- Navigate to `https://YOUR_PROJECT_ID.web.app`
- Configure authentication in Firebase Console

### Usage

1. **Start an engagement:**
   - Open the dashboard
   - Click "Start Engagement"
   - Enter target and scan type
   - **Ensure you have authorization!**

2. **Monitor progress:**
   - View real-time updates in the dashboard
   - Review scan results, validations, and exploitation attempts
   - Make decisions when prompted

3. **Handle decision points:**
   - System will pause for human authorization
   - Choose: Continue, Gather Intelligence, or Stop
   - All actions are logged for compliance

## Agent Details

### Recon Agent
- Performs network reconnaissance using Nmap
- Generates attack hypotheses based on open ports/services
- Publishes findings to Pub/Sub for validation

### Validation Agent
- Validates hypotheses from recon phase
- Checks for common vulnerabilities
- Supports HTTP/HTTPS, SSH, FTP, SMB services

### Amplifier Agent
- Attempts safe exploitation of validated vulnerabilities
- Built on Kali Linux with Metasploit
- Triggers human decision points on success

## Security Considerations

- **IAM**: Each agent runs with minimal required permissions
- **VPC**: Consider deploying within VPC Service Controls
- **Monitoring**: All actions are logged to Firestore
- **Billing**: Set up alerts to prevent runaway costs
- **Authorization**: Always verify target authorization

### IAM Roles

| Agent | Roles |
|-------|-------|
| Recon | pubsub.publisher, datastore.user, storage.objectAdmin |
| Validation | pubsub.subscriber, pubsub.publisher, datastore.user |
| Amplifier | pubsub.subscriber, pubsub.publisher, datastore.user, storage.objectAdmin |
| Workflow | run.invoker, pubsub.publisher, datastore.user |

## Cleanup

```bash
./scripts/cleanup.sh YOUR_PROJECT_ID
```

## Configuration

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | GCP Project ID | Required |
| `region` | GCP Region | us-central1 |
| `zone` | GCP Zone | us-central1-a |
| `environment` | Environment name | dev |

### Agent Configuration

Each agent can be configured through environment variables:

- `PROJECT_ID`: GCP project ID
- `ARTIFACT_BUCKET`: Cloud Storage bucket for artifacts
- `PORT`: Service port (default: 8080)

## API Endpoints

### Recon Agent
- `POST /` - Start reconnaissance scan
- `GET /health` - Health check

### Validation Agent
- `POST /` - Validate hypothesis (Pub/Sub push)
- `GET /health` - Health check

### Amplifier Agent
- `POST /` - Exploit target (Pub/Sub push)
- `GET /health` - Health check

## Development

### Building Agents Locally

```bash
cd agents/recon
docker build -t recon-agent:latest .
docker run -p 8080:8080 recon-agent:latest
```

### Running Dashboard Locally

```bash
cd dashboard
npm install
npm start
```

### Terraform Development

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Contributing

This is a demonstration project. For production use:

1. Implement proper authentication
2. Add encryption for sensitive data
3. Set up comprehensive monitoring
4. Establish incident response procedures
5. Regular security reviews

## Troubleshooting

### Common Issues

1. **API not enabled**: Run `gcloud services enable ...` for required APIs
2. **Permission denied**: Check IAM bindings in Terraform
3. **Container push fails**: Run `gcloud auth configure-docker`
4. **Firebase deploy fails**: Ensure you're logged in with `firebase login`

### Logs

View agent logs:
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

View workflow executions:
```bash
gcloud workflows executions list --workflow=red-team-attack-chain
```

## License

This project is for educational and authorized testing purposes only.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review GCP documentation
3. Open an issue in the repository

---

**Remember**: This system is extremely powerful and must only be used against authorized targets with proper legal authorization. The implementation includes safety measures but requires responsible use by qualified security professionals.
