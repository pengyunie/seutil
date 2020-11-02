import os
import unittest
from github.GithubException import GithubException

from seutil import GitHubUtils
from .TestSupport import TestSupport


class test_GitHubUtils(unittest.TestCase):

    @unittest.skip("Require GitHub token, which is not available on CI")
    def test_search_repos_with_username(self):
        test_user = "google"
        test_repos_1 = GitHubUtils.search_repos("user:{}".format(test_user), language="Java")
        self.assertTrue(len(test_repos_1) > 0)

        test_repos_2 = GitHubUtils.search_repos("user:{} language:Java".format(test_user))
        self.assertTrue(len(test_repos_2) > 0)

        # Query separator "+" will not work
        test_repos_3 = GitHubUtils.search_repos("user:{}+language:Java".format(test_user), max_retry_times=0)
        self.assertTrue(len(test_repos_3) == 0)


if __name__ == '__main__':
    unittest.main()
