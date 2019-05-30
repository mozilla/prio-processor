# The Prio Server Runtime

The application folder contains all of the components that are necessary for
running a Mozilla-compatible Prio server. The back-ends can be replaced for
different deployment configurations.

## Quickstart

### GCP

* Create a new project
* Create a service account and save the credentials locally

export GOOGLE_APPLICATION_CREDENTIALS=<CREDENTIALS_FILE>

# TODO

* Configure GCE to run a docker container with the cli script
* Create a GCS resource
* Trigger the GCE instance to terminate

# Resources

https://cloud.google.com/community/tutorials/managing-gcp-projects-with-terraform
https://cloud.google.com/community/tutorials/getting-started-on-gcp-with-terraform#getting_project_credentials