import os
import shutil
import subprocess
import tempfile
import re
from typing import Dict, Any

from utils.log_manager import LogManager
from utils.git_helper import GitHelper
from utils.config import NEXUS_IQ_URL, NEXUS_SECRET

class NexusHelper:
    def __init__(self, log_manager: LogManager, git_helper: GitHelper):
        self.log_manager = log_manager
        self.git_helper = git_helper
        self.nexus_iq_cli_path = "/opt/nexus-iq-cli/nexus-iq-cli.jar"

    def perform_sca_scan(self, repository_url: str, branch: str) -> Dict[str, Any]:
        temp_repo_path = None
        try:
            # Create temporary directory
            temp_repo_path = tempfile.mkdtemp()
            self.log_manager.debug(f"Cloning {repository_url} (branch: {branch}) into {temp_repo_path}")

            # Clone the repository
            response = self.git_helper.pull_repo(repository_url, branch)
            self.log_manager.debug(f"Successfully cloned {repository_url} into {temp_repo_path}")

            # Prepare Nexus IQ CLI command
            self.log_manager.debug(f"Executing Nexus IQ CLI scan from path: {self.nexus_iq_cli_path}")
            command_args = [
                "java",
                "--add-opens", "java.base/java.lang=ALL-UNNAMED",
                "--add-opens", "java.base/java.nio=ALL-UNNAMED",
                "-jar", self.nexus_iq_cli_path,
                "-a", NEXUS_SECRET,
                "-i", temp_repo_path,
                "-s", NEXUS_IQ_URL
            ]

            process = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                check=False
            )

            scan_output = process.stdout
            scan_error = process.stderr

            # Extract report URL from the scan output
            pattern = r"the detailed report can be viewed online at (https://\S+)"
            match = re.search(pattern, scan_output)

            if match:
                report_url = match.group(1)
                self.log_manager.debug(f"Nexus IQ scan report URL: {report_url}")
            else:
                self.log_manager.warning("Nexus IQ report URL not found in output.")
                report_url = None

            if process.returncode != 0:
                self.log_manager.error(f"Nexus IQ CLI scan failed. Exit code: {process.returncode}")
                self.log_manager.error(f"CLI Output:\n{scan_output}")
                self.log_manager.error(f"CLI Error:\n{scan_error}")
                raise Exception(f"Nexus IQ CLI scan failed. Error: {scan_error.strip() or 'No error message.'}")

            self.log_manager.debug("Nexus IQ CLI scan completed successfully.")
            self.log_manager.debug(f"CLI Output:\n{scan_output}")

            return {"report_url": report_url}

        except Exception as e:
            self.log_manager.exception(f"An error occurred during SCA scan: {str(e)}")
            raise e

        finally:
            if temp_repo_path and os.path.exists(temp_repo_path):
                self.log_manager.debug(f"Cleaning up temporary repository path: {temp_repo_path}")
                shutil.rmtree(temp_repo_path)
