"""Click commands."""
import os
import sys
from glob import glob
from subprocess import call

import click

HERE = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(HERE, os.pardir)
TEST_PATH = os.path.join(PROJECT_ROOT, "tests")

if os.environ.get("FLASK_COVERAGE"):
    import coverage

    COV = coverage.coverage(branch=True, include="flask_conferences/*")
    COV.start()


@click.command()
@click.option(
    "--coverage/--no-coverage",
    default=False,
    is_flag=True,
    help="Run tests under code coverage.",
)
@click.argument("test_name", nargs=-1)
def test(coverage, test_name):
    """Run the tests."""
    import pytest

    if coverage and not os.environ.get("FLASK_COVERAGE"):
        os.environ["FLASK_COVERAGE"] = "1"
        sys.exit(call(sys.argv))

    rv = pytest.main([TEST_PATH, "--verbose"])

    if COV:
        COV.stop
        COV.save()
        print("Coverage Summary")
        COV.report()
        covdir = os.path.join(PROJECT_ROOT, "tmp/coverage")
        COV.html_report(directory=covdir)
        COV.xml_report(directory=covdir)
        print("HTML Version: file://%s/index.html" % covdir)
        COV.erase()

    exit(rv)


@click.command()
@click.option(
    "-f",
    "--fix-imports",
    default=True,
    is_flag=True,
    help="Fix imports using isort, before linting",
)
@click.option(
    "-c",
    "--check",
    default=False,
    is_flag=True,
    help="Don't make any changes to files, just confirm they are formatted correctly",
)
def lint(fix_imports, check):
    """Lint and check code style with black, flake8 and isort."""
    skip = ["node_modules", "requirements", "migrations"]
    root_files = glob("*.py")
    root_directories = [
        name for name in next(os.walk("."))[1] if not name.startswith(".")
    ]
    files_and_directories = [
        arg for arg in root_files + root_directories if arg not in skip
    ]

    def execute_tool(description, *args):
        """Execute a checking tool with its arguments."""
        command_line = list(args) + files_and_directories
        click.echo(f"{description}: {' '.join(command_line)}")
        rv = call(command_line)
        if rv != 0:
            exit(rv)

    isort_args = ["-rc"]
    black_args = []
    if check:
        isort_args.append("-c")
        black_args.append("--check")
    if fix_imports:
        execute_tool("Fixing import order", "isort", *isort_args)
    execute_tool("Formatting style", "black", *black_args)
    execute_tool("Checking code style", "flake8")
