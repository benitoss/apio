"""
  Test for the "apio create" command
"""

from pathlib import Path
from os.path import isfile, exists
from typing import Dict
from configobj import ConfigObj

# -- apio create entry point
from apio.commands.create import cli as cmd_create


# R0801: Similar lines in 2 files
# pylint: disable=R0801
def _check_ini_file(apio_ini: Path, expected_vars: Dict[str, str]) -> None:
    """Assert that apio.ini contains exactly the given vars."""
    # Read the ini file.
    assert isfile(apio_ini)
    conf = ConfigObj(str(apio_ini))
    # Check the expected comment at the top.
    assert "# APIO project configuration file" in conf.initial_comment[0]
    # Check the expected vars.
    assert conf.dict() == {"env": expected_vars}


def test_create(click_cmd_runner, setup_apio_test_env, assert_apio_cmd_ok):
    """Test "apio create" with different parameters"""

    with click_cmd_runner.isolated_filesystem():

        # -- Config the apio test environment
        setup_apio_test_env()

        apio_ini = Path("apio.ini")
        assert not exists(apio_ini)

        # -- Execute "apio create"
        result = click_cmd_runner.invoke(cmd_create)
        assert result.exit_code != 0, result.output
        assert "Error: Missing option" in result.output
        assert not exists(apio_ini)

        # -- Execute "apio create --board missed_board"
        result = click_cmd_runner.invoke(
            cmd_create, ["--board", "missed_board"]
        )
        assert result.exit_code == 1, result.output
        assert "Error: no such board" in result.output
        assert not exists(apio_ini)

        # -- Execute "apio create --board icezum"
        result = click_cmd_runner.invoke(cmd_create, ["--board", "icezum"])
        assert_apio_cmd_ok(result)
        assert "file already exists" not in result.output
        assert "Do you want to replace it?" not in result.output
        assert "Creating apio.ini file ..." in result.output
        assert "was created successfully." in result.output
        _check_ini_file(apio_ini, {"board": "icezum", "top-module": "main"})

        # -- Execute "apio create --board alhambra-ii
        # --                      --top-module my_module" with 'y' input"
        result = click_cmd_runner.invoke(
            cmd_create,
            ["--board", "alhambra-ii", "--top-module", "my_module"],
            input="y",
        )
        assert_apio_cmd_ok(result)
        assert "Warning" in result.output
        assert "file already exists" in result.output
        assert "Do you want to replace it?" in result.output
        assert "was created successfully." in result.output
        _check_ini_file(
            apio_ini, {"board": "alhambra-ii", "top-module": "my_module"}
        )

        # -- Execute "apio create --board icezum
        # --                      --top-module my_module
        # --                      --sayyse" with 'y' input
        result = click_cmd_runner.invoke(
            cmd_create,
            ["--board", "icezum", "--top-module", "my_module", "--sayyes"],
        )
        assert_apio_cmd_ok(result)
        assert "was created successfully." in result.output
        _check_ini_file(
            apio_ini, {"board": "icezum", "top-module": "my_module"}
        )

        # -- Execute "apio create --board alhambra-ii
        # --                      --top-module my_module" with 'n' input
        result = click_cmd_runner.invoke(
            cmd_create,
            ["--board", "alhambra-ii", "--top-module", "my_module"],
            input="n",
        )
        assert result.exit_code != 0, result.output
        assert "Warning" in result.output
        assert "file already exists" in result.output
        assert "Do you want to replace it?" in result.output
        assert "Abort!" in result.output
        _check_ini_file(
            apio_ini, {"board": "icezum", "top-module": "my_module"}
        )
