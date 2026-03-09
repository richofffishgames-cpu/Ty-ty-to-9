output "recon_service_url" {
  value = google_cloud_run_v2_service.recon.uri
}

output "validation_service_url" {
  value = google_cloud_run_v2_service.validation.uri
}

output "amplifier_service_url" {
  value = google_cloud_run_v2_service.amplifier.uri
}

output "workflow_name" {
  value = google_workflows_workflow.attack_chain.name
}

output "firebase_config" {
  value = {
    apiKey    = google_firebase_web_app_config.dashboard.api_key
    authDomain = "${var.project_id}.firebaseapp.com"
    projectId = var.project_id
  }
  sensitive = true
}

output "artifact_bucket" {
  value = google_storage_bucket.artifacts.name
}
