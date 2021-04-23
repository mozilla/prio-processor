variable "server_id" {
  type        = string
  description = "The identifier for the server"
}

variable "suffix" {
  type        = string
  description = "A shared suffix used for the bucket"
}

// Create all of the storage resources necessary for the tests. We choose to
// delete files older than 7 days since these are testing resources.
resource "google_storage_bucket" "private" {
  name                        = "${var.server_id}-private-${var.suffix}"
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

resource "google_storage_bucket" "shared" {
  name                        = "${var.server_id}-shared-${var.suffix}"
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

output "private" {
  value = google_storage_bucket.private.name
}

output "shared" {
  value = google_storage_bucket.shared.name
}
