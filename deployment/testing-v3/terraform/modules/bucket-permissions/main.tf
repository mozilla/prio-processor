resource "google_storage_bucket_iam_member" "private-internal" {
  bucket = var.bucket_private
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_internal}"
}

resource "google_storage_bucket_iam_member" "shared-internal" {
  bucket = var.bucket_shared
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_internal}"
}

resource "google_storage_bucket_iam_member" "shared-external" {
  bucket = var.bucket_shared
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.service_account_external}"
}
