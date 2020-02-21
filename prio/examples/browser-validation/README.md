# Validate Browser Data

This example validates the results from a pilot experiment.

## Usage

Setup
```
$ pipenv lock
$ pipenv sync --dev
$ pipenv shell
```

To test against generated data, run the `generate.py` script.

```
$ python generate.py --path test.batch.json
```

This will generate the corresponding command for validation.
Verify the output of this command before running it.

```
$ python generate.py --path test.batch.json | bash
```

To run against a real browser ping, you can run a command in the following form:
```
$ python main.py \
    --pings sample.batch.json \
    --pubkey-A <HEXKEY> \
    --pvtkey-A <HEXKEY> \
    --pubkey-B <HEXKEY> \
    --pvtkey-B <HEXKEY>
```

The `--pings` argument generally takes a set of json documents; one per line and delimited by a new line.

The ping should be compacted before being presented to the program.
```
# use `jq -c` to compact a json document
$ cat my-ping.json | jq -c . > my-ping.batch.json
```

To run against the parquet dataset, make sure you have AWS credentials with access to the appropriate bucket. To verify that everything is set up correctly:

```
$ aws s3 ls s3://net-mozaws-prod-us-west-2-pipeline-analysis/amiyaguchi/prio/v1
```

Then run the following command:

```
$ python main.py \
    --date 20181007 \
    --pubkey-A <HEXKEY> \
    --pvtkey-A <HEXKEY> \
    --pubkey-B <HEXKEY> \
    --pvtkey-B <HEXKEY>
```

### Docker
This image may also be run via docker. Pass the appropriate environment variables as follows:

```bash
$ make build

$ make test

$ AWS_ACCESS_KEY_ID= \
AWS_SECRET_ACCESS_KEY= \
PRIO_DATE= \
PRIO_PUBKEY_A= \
PRIO_PVTKEY_A= \
PRIO_PUBKEY_B= \
PRIO_PVTKEY_B= \
make run
```