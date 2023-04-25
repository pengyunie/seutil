import math
import traceback
from datetime import datetime
from time import sleep
from typing import *

from github import Github, RateLimitExceededException
from github.GithubException import GithubException
from github.NamedUser import NamedUser
from github.Repository import Repository

from . import _config
from .LoggingUtils import LoggingUtils
from .BashUtils import BashUtils


class GitHubUtils:

    logger = LoggingUtils.get_logger("GitHubUtils", LoggingUtils.DEBUG)

    GITHUB_SEARCH_ITEMS_MAX = 1000
    try:
        DEFAULT_ACCESS_TOKEN = _config.get_config("github_access_token")
        DEFAULT_GITHUB_OBJECT = Github(DEFAULT_ACCESS_TOKEN, per_page=100)
    except:
        DEFAULT_ACCESS_TOKEN = None
        DEFAULT_GITHUB_OBJECT = None
        logger.info("Fail to get github_access_token from config file.  Using GitHubUtils APIs will require compulsory input access_token")
    # end try

    @classmethod
    def get_github(cls, access_token: str = None) -> Github:
        if access_token is None:
            return cls.DEFAULT_GITHUB_OBJECT
        else:
            return Github(access_token)

    class wait_rate_limit:
        """
        Wait for rate limit of the github accessor. For use with "with".
        Use the default github accessor if no argument is given.
        """
        DEFAULT_GITHUB_OBJECT = None
        logger = None

        def __init__(self, github: Github = DEFAULT_GITHUB_OBJECT):
            self.github = github
            return

        def __enter__(self):
            if self.github is None:
                self.github = self.DEFAULT_GITHUB_OBJECT
            # end if

            # Check rate limit
            rate_limit_remain, rate_limit = self.github.rate_limiting
            if rate_limit_remain <= 1:
                self.logger.debug("Rate limit {} / {}".format(rate_limit_remain, rate_limit))
                rate_limit_reset_time = datetime.fromtimestamp(self.github.rate_limiting_resettime)
                rate_limit_wait_seconds = math.ceil((rate_limit_reset_time - datetime.now()).total_seconds()) + 1
                if rate_limit_wait_seconds > 0:
                    self.logger.warning("Rate limit will recover at: {}, will wait for {} seconds.".format(rate_limit_reset_time, rate_limit_wait_seconds))
                    sleep(rate_limit_wait_seconds)
                    self.logger.warning("Rate limit recovered")
                # end if
            # end if
            return self.github

        def __exit__(self, type, value, tb):
            return

    # end class
    wait_rate_limit.DEFAULT_GITHUB_OBJECT = DEFAULT_GITHUB_OBJECT
    wait_rate_limit.logger = logger

    T = TypeVar("T")
    @classmethod
    def ensure_github_api_call(cls, call: Callable[[Github], T], github: Github = DEFAULT_GITHUB_OBJECT, max_retry_times: int = float("inf")) -> T:
        retry_times = 0
        while True:
            try:
                with cls.wait_rate_limit(github) as g:
                    return call(g)
                # end with
            except (GithubException, RateLimitExceededException) as e:
                if e.status == 422:
                    cls.logger.warning("Validation Error. Will not retry.")
                    raise
                else:
                    cls.logger.warning("Unexpected exception during api call: {}".format(traceback.format_exc()))
                    retry_times += 1
                    if retry_times > max_retry_times:
                        cls.logger.warning("Exceeding max retry times {}".format(max_retry_times))
                        raise
                    # end if

                    retry_wait_time = min(retry_times * 30, 600)
                    cls.logger.warning("Will wait {} seconds before retry {}".format(retry_wait_time, retry_times))
                    sleep(retry_wait_time)
            # end try
        # end while

    @classmethod
    def search_repos(cls, q: str = "", sort: str = "stars", order: str = "desc",
                     is_allow_fork: bool = False,
                     max_num_repos: int = GITHUB_SEARCH_ITEMS_MAX,
                     github: Github = DEFAULT_GITHUB_OBJECT,
                     max_retry_times: int = float("inf"),
                     *_, **qualifiers) -> List[Repository]:
        """
        Searches the repos by querying GitHub API v3.
        :return: a list of full names of the repos match the query.
        """
        cls.logger.debug("Search for repos with query {}, sort {}, order {}".format(q, sort, order))
        repos = list()
        num_repos = 0
        repos_iterator = iter(github.search_repositories(q, sort, order, **qualifiers))
        while True:
            try:
                repo = cls.ensure_github_api_call(lambda g: next(repos_iterator), github, max_retry_times)

                # Check fork
                if not is_allow_fork:
                    if repo.fork:
                        continue
                # end if, if

                repos.append(repo)
                num_repos += 1

                # Check number
                if num_repos >= max_num_repos:
                    break
                # end if
            except StopIteration:
                break
            except:
                cls.logger.warning("Unknown exception: {}".format(traceback.format_exc()))
                cls.logger.warning("Returning partial results")
                break
            # end try except
        # end while

        if num_repos < max_num_repos:
            cls.logger.info("Got {}/{} repos".format(num_repos, max_num_repos))
        else:
            cls.logger.info("Got {}/{} repos".format(num_repos, max_num_repos))
        # end if

        return repos

    @classmethod
    def search_users(cls, q: str = "", sort: str = "repositories", order: str = "desc",
                     max_num_users: int = GITHUB_SEARCH_ITEMS_MAX,
                     github: Github = DEFAULT_GITHUB_OBJECT,
                     max_retry_times: int = float("inf"),
                     *_, **qualifiers) -> List[NamedUser]:
        """
        Searches the users by querying GitHub API v3.
        :return: a list of usernames (login) of the users match the query.
        """
        cls.logger.debug("Search for users with query {}, sort {}, order {}".format(q, sort, order))
        users = list()
        num_users = 0
        users_iterator = iter(github.search_users(q, sort, order, **qualifiers))
        while True:
            try:
                user = cls.ensure_github_api_call(lambda g: next(users_iterator), github, max_retry_times)

                users.append(user)
                num_users += 1

                # Check number
                if num_users >= max_num_users:
                    break
                # end if
            except StopIteration:
                break
            except:
                cls.logger.warning("Unknown exception: {}".format(traceback.format_exc()))
                cls.logger.warning("Returning partial results.")
                break
            # end try except
        # end while

        if num_users < max_num_users:
            cls.logger.warning("Got {}/{} users".format(num_users, max_num_users))
        else:
            cls.logger.info("Got {}/{} users".format(num_users, max_num_users))
        # end if

        return users

    @classmethod
    def search_repos_of_language(cls, language: str, max_num_repos: int = float("inf"),
                                 is_allow_fork: bool = False,
                                 max_retry_times: int = float("inf"),
                                 strategies: List[str] = None) -> List[Repository]:
        """
        Searches for all the repos of the language.
        :return: a list of full names of matching repos.
        """
        if strategies is None:
            strategies = ["search_repos", "search_users"]
        # end if

        # Check supported strategies
        supported_strategies = ["search_repos", "search_users", "enum_users"]
        for strategy in strategies:
            assert strategy in supported_strategies, strategy
        # end for

        names_repos = dict()

        try:
            # Strategy 1: search repos (limited to 1000)
            strategy = "search_repos"
            if strategy in strategies:
                cls.logger.info("Using strategy {}".format(strategy))
                new_repos = cls.search_repos("language:{}".format(language), is_allow_fork=is_allow_fork, max_retry_times=max_retry_times, max_num_repos=max_num_repos)
                for repo in new_repos:
                    names_repos[repo.full_name] = repo
                # end for
                cls.logger.warning("Progress {}/{} repos.".format(len(names_repos), max_num_repos))
                if len(names_repos) >= max_num_repos:
                    return list(names_repos.values())
                # end if
            # end if

            # Strategy 2: search users (~37000?)
            strategy = "search_users"
            if strategy in strategies:
                cls.logger.info("Using strategy {}".format(strategy))
                s_users = set()
                # s_users = s_users.union([u.login for u in cls.search_users("language:{}".format(language), sort="repositories", max_retry_times=max_retry_times)])
                s_users = s_users.union([u.login for u in cls.search_users("language:{}".format(language), sort="followers", max_retry_times=max_retry_times)])
                # s_users = s_users.union([u.login for u in cls.search_users("language:{}".format(language), sort="joined", max_retry_times=max_retry_times)])
                users_count = 0
                total_users_count = len(s_users)
                for user in s_users:
                    try:
                        new_repos = cls.search_repos("language:{} user:{}".format(language, user), is_allow_fork=is_allow_fork, max_retry_times=max_retry_times)
                    except GithubException as e:
                        cls.logger.warning("Cannot get the repos of user {}".format(user))
                        continue
                    # end try
                    for repo in new_repos:
                        names_repos[repo.full_name] = repo
                    # end for
                    users_count += 1
                    cls.logger.debug("Progress {}/{} repos, {}/{} users.".format(len(names_repos), max_num_repos, users_count, total_users_count))
                    if len(names_repos) >= max_num_repos:
                        return list(names_repos.values())
                    # end if
                # end for
            # end if

            # Strategy 3: enum users (?)
            strategy = "enum_users"
            if strategy in strategies:
                cls.logger.warning("Strategy {} is not implemented yet.".format(strategy))
                cls.logger.warning("Nothing happens.")
            # end if
        except KeyboardInterrupt as e:
            cls.logger.warning("Interrupted. Returning partial results.")
        finally:
            cls.logger.warning("Got {}/{} repos.".format(len(names_repos), max_num_repos))
            return list(names_repos.values())

    @classmethod
    def is_url_valid_git_repo(cls, url: str) -> bool:
        if BashUtils.run(f"git ls-remote {url}").return_code == 0:
            return True
        else:
            return False
