import click
from .commands import (
    shared_seed,
    keygen,
    random_shares,
    encode_shares,
    verify1,
    verify2,
    aggregate,
    publish,
)


@click.group()
def main(args=None):
    """Command line utility for prio."""
    pass


main.add_command(shared_seed)
main.add_command(keygen)
main.add_command(random_shares)

main.add_command(encode_shares)
main.add_command(verify1)
main.add_command(verify2)
main.add_command(aggregate)
main.add_command(publish)
