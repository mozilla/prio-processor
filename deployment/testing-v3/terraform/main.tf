terraform {
  // When forking this configuration, set the configuration appropriately. A
  // remote backend is a good choice since it can be shared across a team.
  backend "gcs" {
    bucket = "amiyaguchi-prio-processor-v3"
    prefix = "tf-state"
  }
}

variable "project" {
  type    = string
  default = "amiyaguchi-prio-processor-v3"
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

// Create all of the storage resources necessary for the tests. We choose to
// delete files older than 7 days since these are testing resources.
resource "google_storage_bucket" "a-private" {
  name                        = "a-private-${random_id.project.hex}"
  uniform_bucket_level_access = true
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "a-shared" {
  name                        = "a-shared-${random_id.project.hex}"
  uniform_bucket_level_access = true
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "b-private" {
  name                        = "b-private-${random_id.project.hex}"
  uniform_bucket_level_access = true
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "b-shared" {
  name                        = "b-shared-${random_id.project.hex}"
  uniform_bucket_level_access = true
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

// Create the service accounts for the tests
resource "google_service_account" "service-account-admin" {
  account_id   = "service-account-admin"
  display_name = "Service account for the administrator"
}

resource "google_service_account" "service-account-a" {
  account_id   = "service-account-a"
  display_name = "Service account for server A"
}

resource "google_service_account" "service-account-b" {
  account_id   = "service-account-b"
  display_name = "Service account for server B"
}

// Assign service account permissions to each bucket. There are quite a few rules,
// so we break this out into a module.

// The admin account needs to be able to write to the internal bucket. See 
// issue #102 for possible simplification that doesn't require editor access.
resource "google_storage_bucket_iam_member" "admin-a-private" {
  bucket = google_storage_bucket.a-private.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.service-account-admin.email}"
}

resource "google_storage_bucket_iam_member" "admin-b-private" {
  bucket = google_storage_bucket.b-private.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.service-account-admin.email}"
}

module "bucket-permissions-a" {
  source                   = "./modules/bucket-permissions"
  bucket_private           = google_storage_bucket.a-private.name
  bucket_shared            = google_storage_bucket.a-shared.name
  service_account_internal = google_service_account.service-account-a.email
  service_account_external = google_service_account.service-account-b.email
}

module "bucket-permissions-b" {
  source                   = "./modules/bucket-permissions"
  bucket_private           = google_storage_bucket.b-private.name
  bucket_shared            = google_storage_bucket.b-shared.name
  service_account_internal = google_service_account.service-account-b.email
  service_account_external = google_service_account.service-account-a.email
}

// testing whether origin telemetry inserts into BigQuery correctly
resource "google_project_service" "bigquery" {
  service = "bigquery.googleapis.com"
}

resource "google_bigquery_dataset" "telemetry" {
  dataset_id = "telemetry"
  location   = "US"
}

// Grant access to the admin service account
resource "google_project_iam_member" "bigquery-admin" {
  role = "roles/bigquery.admin"
  member = "serviceAccount:${google_service_account.service-account-admin.email}"
}
