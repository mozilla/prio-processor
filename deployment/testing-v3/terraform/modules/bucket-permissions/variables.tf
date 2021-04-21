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
