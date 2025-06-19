import os
import shutil
import git
from git import Repo
from utils.log_manager import LogManager
from utils.config import BITBUCKET_USER, BITBUCKET_TOKEN, GIT_SSL_CAINFO

class GitHelper:
    """
    This class is used to interact with Git/Bitbucket repositories.
    """

    def __init__(self, log_manager: LogManager):
        """
        Constructor
        :param log_manager: Logger instance
        """
        self.log_manager = log_manager

    def pull_repo(self, repository_url: str, branch_name: str) -> str:
        """
        Clones or pulls the latest changes from a Git repository.

        :param repository_url: HTTPS URL of the Bitbucket repository
        :param branch_name: Repository branch to check out
        :return: Success or failure message
        """
        try:
            new_url = repository_url.replace("https://", "")
            repo_url = f"https://{BITBUCKET_USER}:{BITBUCKET_TOKEN}@{new_url}"
            local_repo_path = new_url.split("/")[-1].replace(".git", "")

            if os.path.exists(local_repo_path):
                self.log_manager.debug(f"Directory '{local_repo_path}' already exists. Removing it.")
                shutil.rmtree(local_repo_path)
                self.log_manager.debug(f"Directory '{local_repo_path}' has been removed successfully.")

            self.log_manager.debug(f"Cloning repo '{repository_url}' into '{local_repo_path}'")
            repo = git.Repo.clone_from(repo_url, local_repo_path)
            repo.git.checkout(branch_name)
            repo.remotes.origin.pull()
            self.log_manager.debug(f"Repository '{repository_url}' cloned and branch '{branch_name}' checked out.")
            return "Repository cloned successfully"

        except Exception as e:
            self.log_manager.exception(f"Error while cloning repository '{repository_url}': {str(e)}")
            return "Repository cloning failed"
