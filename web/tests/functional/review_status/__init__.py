# coding=utf-8
# -------------------------------------------------------------------------
#
#  Part of the CodeChecker project, under the Apache License v2.0 with
#  LLVM Exceptions. See LICENSE for license information.
#  SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
#
# -------------------------------------------------------------------------

"""Setup for the test package review_status."""


import os
import shutil
import sys
import uuid

from libtest import codechecker
from libtest import env
from libtest import project

# Test workspace should be initialized in this module.
TEST_WORKSPACE = None


def setup_package():
    """Setup the environment for testing review_status."""

    global TEST_WORKSPACE
    TEST_WORKSPACE = env.get_workspace('review_status')

    os.environ['TEST_WORKSPACE'] = TEST_WORKSPACE

    dir_path = os.path.dirname(os.path.realpath(__file__))
    shutil.copytree(os.path.join(dir_path, 'review_status_files'),
                    os.path.join(TEST_WORKSPACE, 'review_status_files'))

    test_project = 'single_bug'

    test_config = {}

    project_info = project.get_info(test_project)

    test_config['test_project'] = project_info

    skip_list_file = None

    test_env = env.test_env(TEST_WORKSPACE)

    codechecker_cfg = {
        'suppress_file': None,
        'skip_list_file': skip_list_file,
        'check_env': test_env,
        'workspace': TEST_WORKSPACE,
        'checkers': [],
        'analyzers': ['clangsa', 'clang-tidy']
    }

    ret = project.clean(test_project, test_env)
    if ret:
        sys.exit(ret)

    # Start or connect to the running CodeChecker server and get connection
    # details.
    print("This test uses a CodeChecker server... connecting...")
    server_access = codechecker.start_or_get_server()
    server_access['viewer_product'] = 'review_status'
    codechecker.add_test_package_product(server_access, TEST_WORKSPACE)

    # Extend the checker configuration with the server access.
    codechecker_cfg.update(server_access)

    test_project_name = project_info['name'] + '_' + uuid.uuid4().hex

    ret = codechecker.check_and_store(codechecker_cfg,
                                      test_project_name,
                                      project.path(test_project))

    if ret:
        sys.exit(1)
    print("Analyzing the test project was successful.")

    codechecker_cfg['run_names'] = [test_project_name]

    test_config['codechecker_cfg'] = codechecker_cfg

    env.export_test_cfg(TEST_WORKSPACE, test_config)


def teardown_package():
    """Clean up after the test."""

    # TODO: If environment variable is set keep the workspace
    # and print out the path.
    global TEST_WORKSPACE

    check_env = env.import_test_cfg(TEST_WORKSPACE)[
        'codechecker_cfg']['check_env']
    codechecker.remove_test_package_product(TEST_WORKSPACE, check_env)

    print("Removing: " + TEST_WORKSPACE)
    shutil.rmtree(TEST_WORKSPACE, ignore_errors=True)
