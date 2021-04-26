terraform {
  // When forking this configuration, set the configuration appropriately. A
  // remote backend is a good choice since it can be shared across a team.
  backend "gcs" {
    bucket = "amiyaguchi-prio-processor-v4"
    prefix = "tf-state"
  }
}

variable "project" {
  type    = string
  default = "amiyaguchi-prio-processor-v4"
}

variable "region" {
  type    = string
  default = "us-central-1"
}

provider "google" {
  project = var.project
  region  = var.region
}

// Choose a different bucket name if the project changes
resource "random_id" "project" {
  keepers = {
    project = var.project
  }
  byte_length = 8
}

module "bucket-a" {
  source    = "./modules/bucket"
  server_id = "a"
  suffix    = random_id.project.hex
}

module "bucket-b" {
  source    = "./modules/bucket"
  server_id = "b"
  suffix    = random_id.project.hex
}


// Create the service accounts for the tests
resource "google_service_account" "ingest" {
  account_id   = "service-account-ingest"
  display_name = "Service account for the ingestion service"
}

resource "google_service_account" "a" {
  account_id   = "service-account-a"
  display_name = "Service account for server A"
}

resource "google_service_account" "b" {
  account_id   = "service-account-b"
  display_name = "Service account for server B"
}

// Assign service account permissions to each bucket. There are quite a few rules,
// so we break this out into a module.
module "bucket-permissions-a" {
  source                   = "./modules/bucket-permissions"
  bucket_private           = module.bucket-a.private
  bucket_shared            = module.bucket-a.shared
  bucket_ingest            = module.bucket-a.ingest
  service_account_internal = google_service_account.a.email
  service_account_external = google_service_account.b.email
  service_account_ingest   = google_service_account.ingest.email
}

module "bucket-permissions-b" {
  source                   = "./modules/bucket-permissions"
  bucket_private           = module.bucket-b.private
  bucket_shared            = module.bucket-b.shared
  bucket_ingest            = module.bucket-b.ingest
  service_account_internal = google_service_account.b.email
  service_account_external = google_service_account.a.email
  service_account_ingest   = google_service_account.ingest.email
}

// testing whether origin telemetry inserts into BigQuery correctly

// The ingest container will be used for coordination, and gets access to
// server A's private bucket because they are operated by the same entity.
resource "google_storage_bucket_iam_member" "ingest_internal_private" {
  bucket = module.bucket-a.private
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.ingest.email}"
}

resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"
}

resource "google_bigquery_dataset" "telemetry" {
  dataset_id = "telemetry"
  location   = "US"
}

// Grant access to the admin service account
resource "google_project_iam_member" "bigquery-admin" {
  role   = "roles/bigquery.admin"
  member = "serviceAccount:${google_service_account.ingest.email}"
}
