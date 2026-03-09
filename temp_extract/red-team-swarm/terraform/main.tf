# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "pubsub.googleapis.com",
    "workflows.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Pub/Sub Topics
resource "google_pubsub_topic" "recon_hypotheses" {
  name = "recon-hypotheses"
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "validated_targets" {
  name = "validated-targets"
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "foothold_achieved" {
  name = "foothold-achieved"
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "human_decision_point" {
  name = "human-decision-point"
  depends_on = [google_project_service.apis]
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "validation_sub" {
  name  = "validation-subscription"
  topic = google_pubsub_topic.recon_hypotheses.name
  message_retention_duration = "86400s"
  ack_deadline_seconds       = 300
  push_config {
    push_endpoint = google_cloud_run_v2_service.validation.uri
    attributes = {
      x-goog-version = "v1beta1"
    }
  }
}

resource "google_pubsub_subscription" "amplifier_sub" {
  name  = "amplifier-subscription"
  topic = google_pubsub_topic.validated_targets.name
  push_config {
    push_endpoint = google_cloud_run_v2_service.amplifier.uri
  }
}

# Firestore Database (Codex)
resource "google_firestore_database" "codex" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  concurrency_mode = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  depends_on  = [google_project_service.apis]
}

# Cloud Storage Bucket for Artifacts
resource "google_storage_bucket" "artifacts" {
  name          = "${var.project_id}-red-team-artifacts"
  location      = var.region
  force_destroy = true
  versioning {
    enabled = true
  }
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# IAM Service Accounts (Least Privilege)
resource "google_service_account" "recon_sa" {
  account_id   = "recon-agent"
  display_name = "Recon Agent Service Account"
}

resource "google_service_account" "validation_sa" {
  account_id   = "validation-agent"
  display_name = "Validation Agent Service Account"
}

resource "google_service_account" "amplifier_sa" {
  account_id   = "amplifier-agent"
  display_name = "Amplifier Agent Service Account"
}

resource "google_service_account" "workflow_sa" {
  account_id   = "workflow-orchestrator"
  display_name = "Workflow Orchestrator Service Account"
}

# IAM Bindings
resource "google_project_iam_member" "recon_permissions" {
  for_each = toset([
    "roles/pubsub.publisher",
    "roles/datastore.user",
    "roles/storage.objectAdmin"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.recon_sa.email}"
}

resource "google_project_iam_member" "validation_permissions" {
  for_each = toset([
    "roles/pubsub.subscriber",
    "roles/pubsub.publisher",
    "roles/datastore.user"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.validation_sa.email}"
}

resource "google_project_iam_member" "amplifier_permissions" {
  for_each = toset([
    "roles/pubsub.subscriber",
    "roles/pubsub.publisher",
    "roles/datastore.user",
    "roles/storage.objectAdmin"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.amplifier_sa.email}"
}

resource "google_project_iam_member" "workflow_permissions" {
  for_each = toset([
    "roles/run.invoker",
    "roles/pubsub.publisher",
    "roles/datastore.user"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.workflow_sa.email}"
}

# Cloud Run Services
resource "google_cloud_run_v2_service" "recon" {
  name     = "recon-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    service_account = google_service_account.recon_sa.email
    containers {
      image = "gcr.io/${var.project_id}/recon-agent:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "ARTIFACT_BUCKET"
        value = google_storage_bucket.artifacts.name
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    timeout = "3600s"
  }
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service" "validation" {
  name     = "validation-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    service_account = google_service_account.validation_sa.email
    containers {
      image = "gcr.io/${var.project_id}/validation-agent:latest"
      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 50
    }
  }
}

resource "google_cloud_run_v2_service" "amplifier" {
  name     = "amplifier-agent"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  template {
    service_account = google_service_account.amplifier_sa.email
    containers {
      image = "gcr.io/${var.project_id}/amplifier-agent:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "8Gi"
        }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "ARTIFACT_BUCKET"
        value = google_storage_bucket.artifacts.name
      }
    }
    scaling {
      min_instance_count = 0
      max_instance_count = 20
    }
    timeout = "3600s"
  }
}

# Cloud Workflow
resource "google_workflows_workflow" "attack_chain" {
  name            = "red-team-attack-chain"
  region          = var.region
  description     = "Orchestrates red team attack chain"
  service_account = google_service_account.workflow_sa.id
  source_contents = templatefile("${path.module}/../workflows/attack-chain.yaml", {
    project_id = var.project_id
    region     = var.region
    recon_url  = google_cloud_run_v2_service.recon.uri
  })
  depends_on = [google_project_service.apis]
}

# Firebase/Dashboard Setup
resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id
}

resource "google_firebase_web_app" "dashboard" {
  provider     = google-beta
  project      = var.project_id
  display_name = "Red Team Dashboard"
  depends_on = [google_firebase_project.default]
}

resource "google_firebase_web_app_config" "dashboard" {
  provider   = google-beta
  web_app_id = google_firebase_web_app.dashboard.app_id
}
