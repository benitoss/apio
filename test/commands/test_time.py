"""
  Test for the "apio time" command
"""

# -- apio time entry point
from apio.commands.time import cli as apio_time


# R0801: Similar lines in 2 files
# pylint: disable=R0801
def test_time(click_cmd_runner, setup_apio_test_env):
    """Test: apio time
    when no apio.ini file is given
    No additional parameters are given
    """

    with click_cmd_runner.isolated_filesystem():

        # -- Config the apio test environment
        setup_apio_test_env()

        # -- Execute "apio time"
        result = click_cmd_runner.invoke(apio_time)

        # -- Check the result
        assert result.exit_code != 0, result.output
        assert "Info: Project has no apio.ini file" in result.output
        assert "Error: insufficient arguments: missing board" in result.output


def test_time_board(click_cmd_runner, setup_apio_test_env):
    """Test: apio time
    when parameters are given
    """

    with click_cmd_runner.isolated_filesystem():

        # -- Config the apio test environment
        setup_apio_test_env()

        # -- Execute "apio time"
        result = click_cmd_runner.invoke(apio_time, ["--board", "icezum"])

        # -- Check the result
        assert result.exit_code != 0, result.output
        assert "apio packages --install --force oss-cad-suite" in result.output
