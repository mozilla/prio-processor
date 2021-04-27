// create an HMAC pair for each service account

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

resource "google_storage_hmac_key" "internal" {
  service_account_email = var.service_account_internal
}

resource "google_storage_hmac_key" "external" {
  service_account_email = var.service_account_external
}

resource "google_storage_hmac_key" "ingest" {
  service_account_email = var.service_account_ingest
}
