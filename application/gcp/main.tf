variable project_id { default = "amiyaguchi-test-prio" }

provider "google" {
  project = "${var.project_id}"
  region  = "us-west1"
  zone    = "us-west1-a"
}

resource "google_compute_instance" "vm_instance" {
  name         = "prio-instance"
  machine_type = "f1-micro"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network = "default"
    access_config {
    }
  }
}

output "instance_id" {
  value = "${google_compute_instance.vm_instance.self_link}"
}

