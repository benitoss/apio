"""
  Test for the "apio build" command
"""

from os import chdir
from test.conftest import ApioRunner
from apio.commands.build import cli as apio_build


# R0801: Similar lines in 2 files
# pylint: disable=R0801
def test_build_without_apio_init(apio_runner: ApioRunner):
    """Tests build with various valid and invalid apio variation, all tests
    are offline and without any apio package installed."""

    with apio_runner.in_sandbox() as sb:

        # -- Create and change to project dir.
        sb.proj_dir.mkdir()
        chdir(sb.proj_dir)

        # -- Run "apio build" without apio.ini
        result = sb.invoke_apio_cmd(apio_build)
        assert result.exit_code != 0, result.output
        assert "Error: missing project file apio.ini" in result.output


def test_build_with_apio_init(apio_runner: ApioRunner):
    """Tests build with various valid and invalid apio variation, all tests
    are offline and without any apio package installed."""

    with apio_runner.in_sandbox() as sb:

        # -- Create and change to project dir.
        sb.proj_dir.mkdir()
        chdir(sb.proj_dir)

        # -- Run "apio build" with a valid apio.
        sb.write_apio_ini({"board": "alhambra-ii", "top-module": "main"})
        result = sb.invoke_apio_cmd(apio_build, [])
        assert result.exit_code == 1, result.output
        assert "'oss-cad-suite' is not installed" in result.output

        # -- Run "apio build" with a missing board var.
        sb.write_apio_ini({"top-module": "main"})
        result = sb.invoke_apio_cmd(apio_build, [])
        assert result.exit_code == 1, result.output
        assert "missing option 'board'" in result.output

        # -- Run "apio build" with an invalid board
        sb.write_apio_ini({"board": "no-such-board", "top-module": "main"})
        result = sb.invoke_apio_cmd(apio_build, [])
        assert result.exit_code == 1, result.output
        assert "no such board 'no-such-board'" in result.output

        # -- Run "apio build" with an unknown option.
        sb.write_apio_ini(
            {"board": "alhambra-ii", "top-module": "main", "unknown": "xyz"}
        )
        result = sb.invoke_apio_cmd(apio_build, [])
        assert result.exit_code == 1, result.output
        assert "unknown project option 'unknown'" in result.output

        # -- Run "apio build" with no 'top-module' option.
        sb.write_apio_ini({"board": "alhambra-ii"})
        result = sb.invoke_apio_cmd(apio_build, [])
        assert result.exit_code == 1, result.output
        assert "Project file has no 'top-module'" in result.output
        assert "package 'oss-cad-suite' is not installed" in result.output
