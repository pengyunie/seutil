import unittest
from pathlib import Path
from typing import *

from pyutil import IOUtils, BashUtils, LoggingUtils
from pyutil.project import Project
from .TestSupport import TestSupport


class test_project(unittest.TestCase):

    SAMPLE_PROJECTS_PATH = TestSupport.SUBJECTS_DIR / "projects" / "sample-projects.json"

    @classmethod
    def load_sample_projects_database(cls) -> List[Dict]:
        return IOUtils.load(cls.SAMPLE_PROJECTS_PATH)

    @classmethod
    def get_a_test_project(cls) -> Project:
        sample_project_database = cls.load_sample_projects_database()[:1]
        project = Project.from_projects_database(sample_project_database)[0]
        return project

    @classmethod
    def get_test_projects(cls) -> List[Project]:
        sample_projects_database = cls.load_sample_projects_database()
        projects = Project.from_projects_database(sample_projects_database)
        return projects

    def test_clone_and_remove(self):
        project = self.get_a_test_project()
        with TestSupport.get_playground_path():
            Project.set_downloads_dir(Path.cwd()/"_downloads")

            # Clone
            project.clone()
            expected_project_dir = (Path.cwd() / "_downloads/{}".format(project.full_name)).absolute()
            self.assertEqual(str(expected_project_dir), str(project.checkout_dir))
            self.assertTrue(expected_project_dir.is_dir())
            self.assertTrue((expected_project_dir/".git").is_dir())

            # Remove
            project.remove()
            self.assertIsNone(project.checkout_dir)
            self.assertFalse(expected_project_dir.is_dir())
        # end with
        return

    def test_checkout_and_revisions(self):
        project = self.get_a_test_project()
        with TestSupport.get_playground_path():
            Project.set_downloads_dir(Path.cwd() / "_downloads")

            # Clone
            project.clone()
            expected_project_dir = (Path.cwd() / "_downloads/{}".format(project.full_name)).absolute()

            # Get all revisions
            all_revisions = project.get_all_revisions()
            self.assertTrue(len(all_revisions) > 0)
            for revision in all_revisions:
                self.assertTrue(revision != "")
            # end for

            if len(all_revisions) < 2:
                print("Too few revisions (<2) to do testing on checkout. Will skip that.")
                return

            # Checkout to some previous revision
            revision = all_revisions[len(all_revisions) // 2 - 1]
            project.checkout(revision)
            self.assertEqual(revision, project.revision)
        # end with
        return

    def test_dump_all_revisions(self):
        project = self.get_a_test_project()
        with TestSupport.get_playground_path():
            Project.set_downloads_dir(Path.cwd() / "_downloads")
            Project.set_results_dir(Path.cwd() / "_results")

            # Clone
            project.clone()

            # Set up results
            project.init_results()

            # Get all revisions, compare with dumped version
            all_revisions = project.get_all_revisions()
            dumped_all_revisions = project.results.load_meta_result("all_revisions.json")
            self.assertListEqual(all_revisions, dumped_all_revisions)
        # end with
        return

    def test_for_each_revision(self):
        project = self.get_a_test_project()
        with TestSupport.get_playground_path():
            Project.set_downloads_dir(Path.cwd() / "_downloads")
            Project.set_results_dir(Path.cwd() / "_results")

            # Clone
            project.clone()

            # Set up results
            project.init_results()

            # Get all revisions, compare with dumped version
            all_revisions = project.get_all_revisions()

            if len(all_revisions) < 10:
                print("Too few revisions (<10) to do testing on for_each_revision. Will skip that.")
                return

            # For each revision, count number of files
            project.for_each_revision(
                lambda p, r: p.results.dump_revision_result(r, "count_files.json", BashUtils.run("git ls-files | wc -l")),
                all_revisions[-10:]
            )
            project.for_each_revision(
                lambda p, r: self.assertIsNotNone(p.results.load_revision_result(r, "count_files.json")),
                all_revisions[-10:],
                is_auto_checkout=False
            )
        # end with
        return
