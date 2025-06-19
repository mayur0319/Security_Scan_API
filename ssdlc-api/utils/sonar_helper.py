import os
import shutil
import subprocess
import tempfile
import re
import requests
import base64
import time
from typing import Dict, Any, Optional

from utils.log_manager import LogManager
from utils.git_helper import GitHelper
from utils.config import SONAR_HOST_URL, SONAR_TOKEN

class SonarHelper:
    def __init__(self, log_manager: LogManager, git_helper: GitHelper):
        self.log_manager = log_manager
        self.git_helper = git_helper
        self.sonarqube_scanner_path = "pysonar-scanner"
        self.sonarqube_host_url = SONAR_HOST_URL
        self.sonarqube_token = SONAR_TOKEN

        if not self.sonarqube_host_url or not self.sonarqube_token:
            self.log_manager.error("SONAR_HOST_URL and SONAR_TOKEN must be set for SonarQube scan.")
            raise ValueError("SonarQube configuration missing. Please set SONAR_HOST_URL and SONAR_TOKEN.")

    def _create_http_connection(self, api_end_point: str, payload: str, method: str) -> Optional[requests.Response]:
        auth = base64.b64encode(f"{self.sonarqube_token}:".encode()).decode()
        url = f"{self.sonarqube_host_url}/{api_end_point}?{payload}"
        headers = {"Authorization": f"Basic {auth}"}
        self.log_manager.info(f"Connecting to URL: {url} with method: {method}")

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            self.log_manager.info(f"Response: {response.text}")

            if 200 <= response.status_code < 300:
                return response
            elif response.status_code == 400:
                if "A similar key already exists" in response.text:
                    self.log_manager.info("Project already exists in SonarQube. Proceeding with scan.")
                    return None
                else:
                    self.log_manager.error(f"Response content: {response.text}")
                    raise Exception(f"[Error]: {response.status_code}: {response.text}")
            elif response.status_code == 401:
                raise Exception("[Error]: Unauthorized. Check your SonarQube token.")
            else:
                raise Exception(f"[Error]: {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"[Error]: Network or request error: {e}")

    def get_analysis_status_and_url(self, ce_task_id: str, project_key: str) -> Dict[str, Any]:
        max_retries = 10
        retry_delay_seconds = 5

        for i in range(max_retries):
            try:
                self.log_manager.info(f"Polling SonarQube analysis status for task {ce_task_id} (Attempt {i+1}/{max_retries})...")
                response = self._create_http_connection("api/ce/task", f"id={ce_task_id}", "GET")

                if response and response.status_code == 200:
                    task_data = response.json().get("task", {})
                    status = task_data.get("status")
                    self.log_manager.debug(f"Task status for {ce_task_id}: {status}")

                    if status == "SUCCESS":
                        report_url = f"{self.sonarqube_host_url}/dashboard?id={project_key}"
                        self.log_manager.info(f"SonarQube analysis successful. Report URL: {report_url}")
                        return {"status": "success", "report_url": report_url}
                    elif status in ["FAILED", "CANCELED"]:
                        error_message = task_data.get("errorMessage", "No specific error message.")
                        self.log_manager.error(f"SonarQube analysis task {ce_task_id} failed or was canceled: {error_message}")
                        return {"status": "failed", "message": f"SonarQube analysis task failed: {error_message}"}
                    else:
                        self.log_manager.info(f"Task {ce_task_id} is {status}. Retrying in {retry_delay_seconds}s...")
                        time.sleep(retry_delay_seconds)
                else:
                    self.log_manager.warning(f"Failed to get task status for {ce_task_id}. Retrying in {retry_delay_seconds}s...")
                    time.sleep(retry_delay_seconds)
            except Exception as e:
                self.log_manager.error(f"Error polling SonarQube task {ce_task_id}: {e}. Retrying in {retry_delay_seconds}s...")
                time.sleep(retry_delay_seconds)

        self.log_manager.error(f"SonarQube analysis task {ce_task_id} did not complete after {max_retries} retries.")
        return {
            "status": "failed",
            "message": "SonarQube analysis timed out or failed to complete.",
            "report_url": f"{self.sonarqube_host_url}/dashboard?id={project_key}"
        }

    def perform_sonarqube_scan(self, repository_url: str, branch: str, path_to_scan: str = ".", commit_id: Optional[str] = None) -> Dict[str, Any]:
        repo_name = repository_url.split('/')[-1].replace('.git', '')
        project_key = repo_name
        project_name = repo_name

        try:
            self.log_manager.info(f"Ensuring SonarQube project {project_key} exists...")
            project_create_response = self._create_http_connection(
                "api/projects/create",
                f"name={project_name}&project={project_key}",
                "POST"
            )

            if project_create_response is None:
                self.log_manager.info(f"SonarQube project {project_key} already exists or was successfully created.")
            elif project_create_response.status_code != 200:
                self.log_manager.error(f"Failed to create SonarQube project {project_key}. Response: {project_create_response.text}")
                return {"status": "failed", "message": f"Failed to create SonarQube project {project_key}."}

            self.log_manager.debug(f"Cloning {repository_url} branch {branch} for SonarQube scan.")
            cloned_repo_path = self.git_helper.pull_repo(repository_url, branch)
            self.log_manager.debug(f"Successfully cloned into {cloned_repo_path}")

            full_scan_path = os.path.join(cloned_repo_path, path_to_scan)
            if not os.path.isdir(full_scan_path):
                self.log_manager.error(f"Path to scan does not exist: {full_scan_path}")
                return {"status": "failed", "message": f"Path to scan does not exist: {full_scan_path}"}

            sonar_properties = {
                "sonar.projectKey": project_key,
                "sonar.projectName": project_name,
                "sonar.sources": path_to_scan,
                "sonar.host.url": self.sonarqube_host_url,
                "sonar.token": self.sonarqube_token,
                "sonar.scm.provider": "git",
                "sonar.scm.forceReloadAll": "true",
                "sonar.branch.name": branch
            }
            if commit_id:
                sonar_properties["sonar.scm.revision"] = commit_id

            command_args = [self.sonarqube_scanner_path] + [f"-D{key}={value}" for key, value in sonar_properties.items()]

            self.log_manager.debug(f"Running SonarQube scan with pysonar-scanner on project {project_name}...")
            process = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                cwd=cloned_repo_path
            )

            scan_output = process.stdout
            scan_error = process.stderr

            self.log_manager.debug(f"CLI Output:\n{scan_output}")
            self.log_manager.debug(f"CLI Error:\n{scan_error}")

            match_dashboard_success = re.search(r"ANALYSIS SUCCESSFUL, you can find the results at: (https://\S+)", scan_error)
            if match_dashboard_success:
                report_url = match_dashboard_success.group(1)
                self.log_manager.info(f"Extracted SonarQube report URL: {report_url}")
            else:
                self.log_manager.warning("Could not find 'ANALYSIS SUCCESSFUL' URL in scanner output.")
                report_url = None

            return {"report_url": report_url}

        except Exception as e:
            self.log_manager.exception(f"An error occurred during SonarQube scan: {str(e)}")
            return {"status": "failed", "message": str(e)}