variable "bucket_private" {
  type        = string
  description = "The private bucket for the current processor"
}

variable "bucket_shared" {
  type        = string
  description = "The shared bucket for both processors"
}

variable "bucket_ingest" {
  type        = string
  description = "The bucket shared with the ingestion service"
}

variable "service_account_internal" {
  type        = string
  description = "The service account for the current processor"
}

variable "service_account_external" {
  type        = string
  description = "The service account for the co-processor"
}

variable "service_account_ingest" {
  type        = string
  description = "The service account for the ingestor"
}

resource "google_storage_bucket_iam_binding" "private" {
  bucket  = var.bucket_private
  role    = "roles/storage.objectAdmin"
  members = ["serviceAccount:${var.service_account_internal}"]
}

resource "google_storage_bucket_iam_binding" "shared" {
  bucket = var.bucket_shared
  role   = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${var.service_account_internal}",
    "serviceAccount:${var.service_account_external}"
  ]
}

resource "google_storage_bucket_iam_binding" "ingest" {
  bucket = var.bucket_ingest
  role   = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${var.service_account_internal}",
    "serviceAccount:${var.service_account_ingest}"
  ]
}
