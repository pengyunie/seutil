import math
import os
import traceback
from datetime import datetime
from time import sleep
from typing import Callable, List, TypeVar

from github import Github, RateLimitExceededException
from github.GithubException import GithubException
from github.NamedUser import NamedUser
from github.Repository import Repository

from . import bash, log

logger = log.get_logger(__name__, log.INFO)


class GitHubUtils:
    GITHUB_SEARCH_ITEMS_MAX = 1000

    DEFAULT_GITHUB_OBJECT = (
        Github(os.environ["SU_GITHUB_ACCESS_TOKEN"], per_page=100) if "SU_GITHUB_ACCESS_TOKEN" in os.environ else None
    )

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

        def __init__(self, github: Github = DEFAULT_GITHUB_OBJECT):
            self.github = github
            return

        def __enter__(self):
            if self.github is None:
                self.github = self.DEFAULT_GITHUB_OBJECT

            # Check rate limit
            rate_limit_remain, rate_limit = self.github.rate_limiting
            if rate_limit_remain <= 1:
                logger.debug(f"Rate limit {rate_limit_remain}/{rate_limit}")
                rate_limit_reset_time = datetime.fromtimestamp(self.github.rate_limiting_resettime)
                rate_limit_wait_seconds = math.ceil((rate_limit_reset_time - datetime.now()).total_seconds()) + 1
                if rate_limit_wait_seconds > 0:
                    logger.warning(
                        f"Rate limit will recover at: {rate_limit_reset_time}, wait for {rate_limit_wait_seconds}s."
                    )
                    sleep(rate_limit_wait_seconds)
                    logger.warning("Rate limit recovered")
            return self.github

        def __exit__(self, type, value, tb):
            return

    wait_rate_limit.DEFAULT_GITHUB_OBJECT = DEFAULT_GITHUB_OBJECT

    T = TypeVar("T")

    @classmethod
    def ensure_github_api_call(
        cls, call: Callable[[Github], T], github: Github = DEFAULT_GITHUB_OBJECT, max_retry_times: int = float("inf")
    ) -> T:
        retry_times = 0
        while True:
            try:
                with cls.wait_rate_limit(github) as g:
                    return call(g)
            except (GithubException, RateLimitExceededException) as e:
                if e.status == 422:
                    logger.warning("Validation Error. Will not retry.")
                    raise
                else:
                    logger.warning(f"Unexpected exception during api call: {traceback.format_exc()}")
                    retry_times += 1
                    if retry_times > max_retry_times:
                        logger.warning(f"Exceeding max retry times {max_retry_times}")
                        raise

                    retry_wait_time = min(retry_times * 30, 600)
                    logger.warning(f"Will wait {retry_wait_time} seconds before retry {retry_times}")
                    sleep(retry_wait_time)

    @classmethod
    def search_repos(
        cls,
        q: str = "",
        sort: str = "stars",
        order: str = "desc",
        is_allow_fork: bool = False,
        max_num_repos: int = GITHUB_SEARCH_ITEMS_MAX,
        github: Github = DEFAULT_GITHUB_OBJECT,
        max_retry_times: int = float("inf"),
        *_,
        **qualifiers,
    ) -> List[Repository]:
        """
        Searches the repos by querying GitHub API v3.
        :return: a list of full names of the repos match the query.
        """
        logger.debug(f"Search for repos with query {q}, sort {sort}, order {order}")
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

                repos.append(repo)
                num_repos += 1

                # Check number
                if num_repos >= max_num_repos:
                    break
            except StopIteration:
                break
            except Exception:
                logger.warning(f"Unknown exception: {traceback.format_exc()}")
                logger.warning("Returning partial results")
                break

        logger.info(f"Got {num_repos}/{max_num_repos} repos")

        return repos

    @classmethod
    def search_users(
        cls,
        q: str = "",
        sort: str = "repositories",
        order: str = "desc",
        max_num_users: int = GITHUB_SEARCH_ITEMS_MAX,
        github: Github = DEFAULT_GITHUB_OBJECT,
        max_retry_times: int = float("inf"),
        *_,
        **qualifiers,
    ) -> List[NamedUser]:
        """
        Searches the users by querying GitHub API v3.
        :return: a list of usernames (login) of the users match the query.
        """
        logger.debug(f"Search for users with query {q}, sort {sort}, order {order}")
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
            except StopIteration:
                break
            except Exception:
                logger.warning(f"Unknown exception: {traceback.format_exc()}")
                logger.warning("Returning partial results.")
                break

        logger.info(f"Got {num_users}/{max_num_users} users")

        return users

    @classmethod
    def search_repos_of_language(
        cls,
        language: str,
        max_num_repos: int = float("inf"),
        is_allow_fork: bool = False,
        max_retry_times: int = float("inf"),
        strategies: List[str] = None,
    ) -> List[Repository]:
        """
        Searches for all the repos of the language.
        :return: a list of full names of matching repos.
        """
        if strategies is None:
            strategies = ["search_repos", "search_users"]

        # Check supported strategies
        supported_strategies = ["search_repos", "search_users", "enum_users"]
        for strategy in strategies:
            assert strategy in supported_strategies, strategy

        names_repos = dict()

        try:
            # Strategy 1: search repos (limited to 1000)
            strategy = "search_repos"
            if strategy in strategies:
                logger.info(f"Using strategy {strategy}")
                new_repos = cls.search_repos(
                    f"language:{language}",
                    is_allow_fork=is_allow_fork,
                    max_retry_times=max_retry_times,
                    max_num_repos=max_num_repos,
                )
                for repo in new_repos:
                    names_repos[repo.full_name] = repo
                logger.info(f"Progress {len(names_repos)}/{max_num_repos} repos.")
                if len(names_repos) >= max_num_repos:
                    return list(names_repos.values())

            # Strategy 2: search users (~37000?)
            strategy = "search_users"
            if strategy in strategies:
                logger.info(f"Using strategy {strategy}")
                s_users = set()
                # sort can be chosen from {followers, repositories, joined}
                s_users = s_users.union(
                    [
                        u.login
                        for u in cls.search_users(
                            f"language:{language}", sort="followers", max_retry_times=max_retry_times
                        )
                    ]
                )
                users_count = 0
                total_users_count = len(s_users)
                for user in s_users:
                    try:
                        new_repos = cls.search_repos(
                            f"language:{language} user:{user}",
                            is_allow_fork=is_allow_fork,
                            max_retry_times=max_retry_times,
                        )
                    except GithubException:
                        logger.warning(f"Cannot get the repos of user {user}")
                        continue
                    for repo in new_repos:
                        names_repos[repo.full_name] = repo
                    users_count += 1
                    logger.debug(
                        f"Progress {len(names_repos)}/{max_num_repos} repos, {users_count}/{total_users_count} users."
                    )
                    if len(names_repos) >= max_num_repos:
                        return list(names_repos.values())

            # Strategy 3: enum users (?)
            strategy = "enum_users"
            if strategy in strategies:
                logger.warning(f"Strategy {strategy} is not implemented yet.")
                logger.warning("Nothing happens.")
        except KeyboardInterrupt:
            logger.warning("Interrupted. Returning partial results.")
        finally:
            logger.warning(f"Got {len(names_repos)}/{max_num_repos} repos.")
            return list(names_repos.values())

    @classmethod
    def is_url_valid_git_repo(cls, url: str) -> bool:
        if bash.run(f"git ls-remote {url}").returncode == 0:
            return True
        else:
            return False
