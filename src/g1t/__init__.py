import click

@click.command()
@click.option("--name", default="World", help="Name to greet.")
def main(name) -> int:
    print(f"Hello {name}.")
    return 0
