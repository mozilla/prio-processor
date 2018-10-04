# Validate Browser Data

This example validates the results from a pilot experiment.

## Usage

Setup
```
$ pipenv lock
$ pipenv sync --dev
$ pipenv shell
```

To run against a single ping:
```
$ python main.py \
    --ping bug-1496552-prio-buildid.json \
    --date 20181002 \
    --pubkey-A <HEXKEY> \
    --pvtkey-A <HEXKEY> \
    --pubkey-B <HEXKEY> \
    --pvtkey-B <HEXKEY>
```
Note that the `--date` option is ignored in this case.

To run against the parquet dataset, make sure you have AWS credentials with access to the appropriate bucket. To verify that everything is set up correctly:

```
$ aws s3 ls s3://net-mozaws-prod-us-west-2-pipeline-analysis/amiyaguchi/prio/v1
```

Then run the following command:

```
$ python main.py \
    --date 20181002 \
    --pubkey-A <HEXKEY> \
    --pvtkey-A <HEXKEY> \
    --pubkey-B <HEXKEY> \
    --pvtkey-B <HEXKEY>
```