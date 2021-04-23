variable "bucket_private" {
  type        = string
  description = "The private bucket for the current processor"
}

variable "bucket_shared" {
  type        = string
  description = "The shared bucket for both processors"
}

variable "service_account_internal" {
  type        = string
  description = "The service account for the current processor"
}

variable "service_account_external" {
  type        = string
  description = "The service account for the co-processor"
}

variable "service_account_admin" {
  type        = string
  description = "The service account for the admin"
}

// The admin account needs to be able to write to the internal bucket. See 
// issue #102 for possible simplification that doesn't require editor access.
resource "google_storage_bucket_iam_binding" "private" {
  bucket = var.bucket_private
  role   = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${var.service_account_internal}",
    "serviceAccount:${var.service_account_admin}"
  ]
}

resource "google_storage_bucket_iam_binding" "shared" {
  bucket = var.bucket_shared
  role   = "roles/storage.objectAdmin"
  members = [
    "serviceAccount:${var.service_account_internal}",
    "serviceAccount:${var.service_account_external}"
  ]
}

