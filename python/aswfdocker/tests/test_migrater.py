# SPDX-License-Identifier: Apache-2.0
"""
Tests for the migrate command
"""
import unittest
import logging

from click.testing import CliRunner

from aswfdocker import migrater, constants
from aswfdocker.cli import aswfdocker


class TestMigrater(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_migrate_nofilter(self):
        m = migrater.Migrater("src", "dst")
        m.gather("", "")
        self.assertGreater(len(m.migration_list), 10)

    def test_migrate_pkgfilter(self):
        m = migrater.Migrater("src", "dst")
        m.gather("openexr", "")
        self.assertEqual(len(m.migration_list), 3)

    def test_migrate_versionfilter(self):
        m = migrater.Migrater("src", "dst")
        m.gather("openexr", "2019")
        current_version = constants.VERSIONS[constants.ImageType.PACKAGE]["openexr"][1]
        self.assertEqual(len(m.migration_list), 1)
        minfo = m.migration_list[0]
        self.assertEqual(minfo.image, "ci-package-openexr")
        self.assertEqual(minfo.version, "2019.1")
        self.assertEqual(
            minfo.source,
            f"{constants.DOCKER_REGISTRY}/src/ci-package-openexr:{current_version}",
        )
        self.assertEqual(
            minfo.destination,
            f"{constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version}",
        )

        m.migrate(dry_run=True)
        self.assertEqual(
            m.cmds,
            [
                f"docker pull {constants.DOCKER_REGISTRY}/src/ci-package-openexr:{current_version}",
                f"docker tag {constants.DOCKER_REGISTRY}/src/ci-package-openexr:{current_version} {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version}",
                f"docker tag {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version} {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:2019",
                f"docker tag {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version} {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:latest",
                f"docker push {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version}",
            ],
        )


class TestMigraterCli(unittest.TestCase):
    def setUp(self):
        logging.getLogger("").handlers = []

    def test_migrate_cli(self):
        runner = CliRunner()
        result = runner.invoke(
            aswfdocker.cli,
            [
                "migrate",
                "--from",
                "src",
                "--to",
                "dst",
                "--package",
                "openexr",
                "--version",
                "2019",
                "--dry-run",
            ],
            input="y\n",
        )
        self.assertEqual(result.exit_code, 0)
        current_version = constants.VERSIONS[constants.ImageType.PACKAGE]["openexr"][1]
        self.assertEqual(
            result.output,
            f"""Are you sure you want to migrate the following 1 packages?
{constants.DOCKER_REGISTRY}/src/ci-package-openexr:{current_version} -> {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version}
 [y/N]: y
INFO:aswfdocker.migrater:Migrating {constants.DOCKER_REGISTRY}/src/ci-package-openexr:{current_version} -> {constants.DOCKER_REGISTRY}/dst/ci-package-openexr:{current_version}
""",
        )
