# -*- coding: utf-8 -*-
# -- This file is part of the Apio project
# -- (C) 2016-2018 FPGAwars
# -- Author Jesús Arroyo
# -- Licence GPLv2
# -- Derived from:
# ---- Platformio project
# ---- (C) 2014-2016 Ivan Kravets <me@ikravets.com>
# ---- Licence Apache v2
"""Utility functions related to apio packages."""

from typing import List, Callable, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import os
import sys
import click
import semantic_version
from apio import util
from apio.profile import Profile
from apio.resources import Resources


@dataclass(frozen=True)
class EnvMutations:
    """Contains mutations to the system env."""

    # -- PATH items to add.
    paths: List[str]
    # -- Vars name/value paris.
    vars: List[Tuple[str, str]]


@dataclass(frozen=True)
class _PackageDesc:
    """Represents an entry in the packages table."""

    # -- Package folder name. E.g. "tools-oss-cad-suite"
    folder_name: str
    # -- True if the package is available for the current platform.
    platform_match: bool
    # -- A function to set the env for this package.
    env_func: Callable[[Path], EnvMutations]


def _get_env_mutations_for_packages(resources: Resources) -> EnvMutations:
    """Collects the env mutation for each of the defined packages,
    in the order they are defined."""

    result = EnvMutations([], [])
    for _, package_config in resources.platform_packages.items():
        # -- Get the json 'env' section. We require it, even if it's empty,
        # -- for clarity reasons.
        assert "env" in package_config
        package_env = package_config["env"]

        # -- Collect the path values.
        path_list = package_env.get("path", [])
        result.paths.extend(path_list)

        # -- Collect the env vars (name, value) pairs.
        vars_section = package_env.get("vars", {})
        for var_name, var_value in vars_section.items():
            result.vars.append((var_name, var_value))

    return result


def _dump_env_mutations(mutations: EnvMutations) -> None:
    """For debugging. Delete once stabalizing the new oss-cad-suite on
    windows."""
    click.secho("Envirnment settings:", fg="magenta")

    # -- Print PATH mutations.
    windows = util.is_windows()
    for p in reversed(mutations.paths):
        styled_name = click.style("PATH", fg="magenta")
        if windows:
            click.echo(f"@set {styled_name}={p};%PATH%")
        else:
            click.echo(f'{styled_name}="{p}:$PATH"')

    # -- Print vars mutations.
    for name, val in mutations.vars:
        styled_name = click.style(name, fg="magenta")
        if windows:
            click.echo(f"@set {styled_name}={val}")
        else:
            click.echo(f'{styled_name}="{val}"')


def _apply_env_mutations(mutations: EnvMutations) -> None:
    """Apply a given set of env mutations, while preserving their order."""

    # -- Apply the path mutations, while preserving order.
    old_val = os.environ["PATH"]
    items = mutations.paths + [old_val]
    new_val = os.pathsep.join(items)
    os.environ["PATH"] = new_val

    # -- Apply the vars mutations, while preserving order.
    for name, value in mutations.vars:
        os.environ[name] = value


# -- A static flag that is used to make sure we set the env only once.
# -- This is to avoid extending the $PATH variable multiple time with the
# -- same directories.
__ENV_ALREADY_SET_FLAG = False


def set_env_for_packages(resources: Resources, verbose: bool = False) -> None:
    """Sets the environment variables for using all the that are
    available for this platform, even if currently not installed.

    The function sets the environment only on first call and in latter calls
    skips the operation silently.
    """
    # pylint: disable=global-statement
    global __ENV_ALREADY_SET_FLAG

    # -- Collect the env mutations for all packages.
    mutations = _get_env_mutations_for_packages(resources)

    if verbose:
        _dump_env_mutations(mutations)

    # -- If this is the first call, apply the mutations. These mutations are
    # -- temporary for the lifetime of this process and does not affect the
    # -- user's shell environment. The mutations are also inheritated by
    # -- child processes such as the scons processes.
    if not __ENV_ALREADY_SET_FLAG:
        _apply_env_mutations(mutations)
        __ENV_ALREADY_SET_FLAG = True
        if not verbose:
            click.secho("Setting the envinronment.")


def check_required_packages(
    required_packages_names: List[str], resources: Resources
) -> None:
    """Checks that the packages whose names are in 'packages_names' are
    installed and have a version that meets the requirements. If any error,
    it prints an error message and aborts the program with an error status
    code.
    """

    profile = Profile()
    installed_packages = profile.packages
    spec_packages = resources.distribution.get("packages")

    # -- Check packages
    for package_name in required_packages_names:
        # -- Package name must be in all_packages. Otherwise it's a programming
        # -- error.
        if package_name not in resources.all_packages:
            raise RuntimeError(f"Unknown package named [{package_name}]")

        # -- Skip if packages is not applicable to this platform.
        if package_name not in resources.platform_packages:
            continue

        # -- The package is applicable to this platform. Check installed
        # -- version, if at all.
        current_version = installed_packages.get(package_name, {}).get(
            "version", None
        )

        # -- Check the installed version against the required version.
        spec_version = spec_packages.get(package_name, "")
        _check_required_package(
            package_name, current_version, spec_version, resources
        )


def _check_required_package(
    package_name: str,
    current_version: Optional[str],
    spec_version: str,
    resources: Resources,
) -> None:
    """Checks that the package with the given packages is installed and
    has a version that meets the requirements. If any error, it prints an
    error message and exists with an error code.

    'package_name' - the package name, e.g. 'oss-cad-suite'.
    'current_version' - the version of the install package or None if not
        installed.
    'spec_version' - a specification of the required version.
    'resources' - the apio resources.
    """
    # -- Case 1: Package is not installed.
    if current_version is None:
        click.secho(
            f"Error: package '{package_name}' is not installed.", fg="red"
        )
        _show_package_install_instructions(package_name)
        sys.exit(1)

    # -- Case 2: Version does not match requirmeents.
    if not _version_matches(current_version, spec_version):
        click.secho(
            f"Error: package '{package_name}' version {current_version}"
            " does not\n"
            f"match the requirement for version {spec_version}.",
            fg="red",
        )

        _show_package_install_instructions(package_name)
        sys.exit(1)

    # -- Case 3: The package's directory does not exist.
    package_dir = resources.get_package_dir(package_name)
    if package_dir and not package_dir.is_dir():
        message = f"Error: package '{package_name}' is installed but missing"
        click.secho(message, fg="red")
        _show_package_install_instructions(package_name)
        sys.exit(1)


def _version_matches(current_version: str, spec_version: str) -> bool:
    """Tests if a given version satisfy the semantic version constraints
    * INPUTS:
      - version: Package version (Ex. '0.0.9')
      - spec_version: semantic version constraint (Ex. '>=0.0.1')
    * OUTPUT:
      - True: Version ok!
      - False: Version not ok! or incorrect version number
    """

    # -- Build a semantic version object
    spec = semantic_version.SimpleSpec(spec_version)

    # -- Check it!
    try:
        semver = semantic_version.Version(current_version)

    # -- Incorrect version number
    except ValueError:
        return False

    # -- Check the version (True if the semantic version is satisfied)
    return semver in spec


def _show_package_install_instructions(package_name: str):
    """Prints hints on how to install a package with a given name."""

    click.secho(
        "Please run:\n"
        f"   apio packages --install --force {package_name}\n"
        "or:\n"
        "   apio packages --install --force",
        fg="yellow",
    )