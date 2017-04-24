import unittest
import os

import fudge
from fudge.inspector import arg

from fabric.contrib import project


class UploadProjectTestCase(unittest.TestCase):
    """Test case for :func: `fabric.contrib.project.upload_project`."""

    fake_tmp = "testtempfolder"


    def setUp(self):
        fudge.clear_expectations()

        # We need to mock out run, local, and put

        self.fake_run = fudge.Fake('project.run', callable=True)
        self.patched_run = fudge.patch_object(
                               project,
                               'run',
                               self.fake_run
                           )

        self.fake_local = fudge.Fake('local', callable=True)
        self.patched_local = fudge.patch_object(
                                 project,
                                 'local',
                                 self.fake_local
                             )

        self.fake_put = fudge.Fake('put', callable=True)
        self.patched_put = fudge.patch_object(
                               project,
                               'put',
                               self.fake_put
                           )

        # We don't want to create temp folders
        self.fake_mkdtemp = fudge.Fake(
                                'mkdtemp',
                                expect_call=True
                            ).returns(self.fake_tmp)
        self.patched_mkdtemp = fudge.patch_object(
                                   project,
                                   'mkdtemp',
                                   self.fake_mkdtemp
                               )


    def tearDown(self):
        self.patched_run.restore()
        self.patched_local.restore()
        self.patched_put.restore()

        fudge.clear_expectations()


    @fudge.with_fakes
    def test_temp_folder_is_used(self):
        """A unique temp folder is used for creating the archive to upload."""

        # Exercise
        project.upload_project()


    @fudge.with_fakes
    def test_project_is_archived_locally(self):
        """The project should be archived locally before being uploaded."""

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_local.with_args(arg.startswith("tar -czf")).next_call()

        # Exercise
        project.upload_project()


    @fudge.with_fakes
    def test_current_directory_is_uploaded_by_default(self):
        """By default the project uploaded is the current working directory."""

        cwd_path, cwd_name = os.path.split(os.getcwd())

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_local.with_args(
            arg.endswith("-C %s %s" % (cwd_path, cwd_name))
        ).next_call()

        # Exercise
        project.upload_project()


    @fudge.with_fakes
    def test_path_to_local_project_can_be_specified(self):
        """It should be possible to specify which local folder to upload."""

        project_path = "path/to/my/project"

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_local.with_args(
            arg.endswith("-C path/to/my project")
        ).next_call()

        # Exercise
        project.upload_project(local_dir=project_path)


    @fudge.with_fakes
    def test_path_to_local_project_no_separator(self):
        """Local folder can have no path separator (in current directory)."""

        project_path = "testpath"

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_local.with_args(
            arg.endswith("-C . testpath")
        ).next_call()

        # Exercise
        project.upload_project(local_dir=project_path)


    @fudge.with_fakes
    def test_path_to_local_project_can_end_in_separator(self):
        """A local path ending in a separator should be handled correctly."""

        project_path = "path/to/my"
        base = "project"

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_local.with_args(
            arg.endswith("-C %s %s" % (project_path, base))
        ).next_call()

        # Exercise
        project.upload_project(local_dir="%s/%s/" % (project_path, base))


    @fudge.with_fakes
    def test_default_remote_folder_is_home(self):
        """Project is uploaded to remote home by default."""

        local_dir = "folder"

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_put.with_args(
            "%s/folder.tar.gz" % self.fake_tmp, "folder.tar.gz", use_sudo=False
        ).next_call()

        # Exercise
        project.upload_project(local_dir=local_dir)

    @fudge.with_fakes
    def test_path_to_remote_folder_can_be_specified(self):
        """It should be possible to specify which local folder to upload to."""

        local_dir = "folder"
        remote_path = "path/to/remote/folder"

        # local() is called more than once so we need an extra next_call()
        # otherwise fudge compares the args to the last call to local()
        self.fake_put.with_args(
            "%s/folder.tar.gz" % self.fake_tmp, "%s/folder.tar.gz" % remote_path, use_sudo=False
        ).next_call()

        # Exercise
        project.upload_project(local_dir=local_dir, remote_dir=remote_path)

