# Testing configuration for v3 containers

This directory contains terraform configuration to bring relevant resources for
an integration test of the prio-processor v3.x containers.

To create a new project that uses the same configuration, change the terraform
backend appropriately. Here, the state is placed into a storage bucket that has
been created beforehand. Ensure the project has also been created. Then:

```bash
cd terraform

# if you're choosing a different project or change any modules
terraform init

# apply any changes
terraform apply
```
