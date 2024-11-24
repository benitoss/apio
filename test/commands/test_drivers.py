"""
  Test for the "apio drivers" command
"""

# -- apio drivers entry point
from apio.commands.drivers import cli as apio_drivers


def test_drivers(click_cmd_runner, assert_apio_cmd_ok, setup_apio_test_env):
    """Test "apio drivers" """

    with click_cmd_runner.isolated_filesystem():

        # -- Config the apio test environment
        setup_apio_test_env()

        # -- Execute "apio drivers"
        result = click_cmd_runner.invoke(apio_drivers)
        assert_apio_cmd_ok(result)

        # -- Execute "apio --ftdi-install, --serial-install"
        result = click_cmd_runner.invoke(
            apio_drivers, ["--ftdi-install", "--serial-install"]
        )
        assert result.exit_code == 1, result.output
        assert (
            "Error: [--ftdi-install, --serial-install] "
            "are mutually exclusive" in result.output
        )
