import sys
import click


def common_options(func):
    func = click.option("--bucket", required=True, help="")(func)
    func = click.option("--prefix", required=True, help="")(func)
    func = click.option("--server-id", required=True, help="")(func)
    func = click.option("--public-key-A", required=True, help="")(func)
    func = click.option("--public-key-B", required=True, help="")(func)
    func = click.option("--private-key", required=True, help="")(func)
    func = click.option("--output", required=True, help="")(func)
    return func


def input_internal_option(func):
    return click.option("--input-internal", required=True, help="")(func)


def input_external_option(func):
    return click.option("--input-external", required=True, help="")(func)


@click.command()
@common_options
@input_internal_option
def verify1():
    """Decode a batch of shares"""
    click.echo("Running create_verify1")


@click.command()
@common_options
@input_internal_option
@input_external_option
def verify2():
    """Verify a batch of SNIPs"""
    click.echo("Running create_verify2")


@click.command()
@common_options
@input_internal_option
@input_external_option
def aggregate():
    """Generate an aggregate share from a batch of verified SNIPs"""
    click.echo("Running aggregate")


@click.command()
@common_options
@input_internal_option
@input_external_option
def publish():
    """Generate a final aggregate and remap data to a content blocklist"""
    click.echo("Running publish")


@click.group()
def main(args=None):
    """Command line utility for prio."""
    pass


main.add_command(verify1)
main.add_command(verify2)
main.add_command(aggregate)
main.add_command(publish)

if __name__ == "__main__":
    sys.exit(main())
