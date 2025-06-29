from fastapi import FastAPI, HTTPException, Query, Body, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import AnyUrl, BaseModel
from typing import Dict, Optional, Any
from dotenv import load_dotenv
import os
import shutil
import git
import json
from git import Repo

from utils.log_manager import LogManager
from utils.git_helper import GitHelper
from utils.wiz_helper import WizHelper
from utils.crane_utils import CraneUtil
from utils.post_helper import PostHelper
from utils.config import SIGNATURE_STORE_ENDPOINT, SUPPORTED_TOOLS
from utils.nexus_helper import NexusHelper
from utils.sonar_helper import SonarHelper

# Load environment variables
load_dotenv()

# Initialize Helpers
log_manager = LogManager('SSDLC SCANNING API')
git_helper = GitHelper(log_manager)
wiz_helper = WizHelper(log_manager=log_manager, git_helper=git_helper)
crane_helper = CraneUtil(log_manager)
post_helper = PostHelper(log_manager)
nexus_iq_scanner = NexusHelper(log_manager=log_manager, git_helper=git_helper)
sonarqube_scanner = SonarHelper(log_manager=log_manager, git_helper=git_helper)

# Initialize FastAPI app
app = FastAPI(
    title="SSDLC Scanning APIs",
    description="Scanning capabilities from SSDLC",
    version="1.0.1"
)

@app.get("/")
async def read_root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    return RedirectResponse(url="/v1/health")

@app.get("/v1/health")
async def health_check_v1():
    return JSONResponse(content={"status": "healthy"})

@app.get("/v1")
async def read_root_v1():
    return "Welcome to ssdlc-api, Please hit /docs for a list of supported endpoints"

@app.get("/v1/DockerFileScan")
async def docker_file_scan_v1(
    bitbucketRepo: AnyUrl = "",
    branch: str = "develop",
    dockerfilePath: str = ".",
    Metadata: Optional[str] = Query(None)
):
    try:
        Metadata_dict = json.loads(Metadata) if Metadata else {}
        if not isinstance(Metadata_dict, dict):
            raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")

    repo_path = bitbucketRepo.split("/")[-1].replace(".git", "")
    git_helper.pull_repo(repository_url=bitbucketRepo, branch_name=branch)
    dockerfile_path = f"{repo_path}/{dockerfilePath}"

    report = wiz_helper.perform_docker_file_scan(dockerFilePath=dockerfile_path)

    signature = {
        "ScanSource": "ssdlc-scan-api",
        "ScanType": "DockerFileScan",
        "Reporturl": report,
        "RepoUrl": bitbucketRepo,
        "RepoName": repo_path,
        "BranchName": branch,
        "Metadata": Metadata_dict
    }

    try:
        post_helper.send_scan_results(signature)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Failed to send scan results to signature store on {SIGNATURE_STORE_ENDPOINT}")

    return {"Reporturl": report}

@app.get("/v1/LacScan")
async def lac_scan_v1(
    bitbucketRepo: AnyUrl,
    branch: str = "develop",
    pathToScan: str = ".",
    Metadata: Optional[str] = Query(None)
):
    try:
        Metadata_dict = json.loads(Metadata) if Metadata else {}
        if not isinstance(Metadata_dict, dict):
            raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")

    repo_path = bitbucketRepo.split("/")[-1].replace(".git", "")
    git_helper.pull_repo(repository_url=bitbucketRepo, branch_name=branch)
    scan_path = f"{repo_path}/{pathToScan}"

    report = wiz_helper.perform_iac_scan(path_to_scan=scan_path)

    signature = {
        "ScanSource": "ssdlc-scan-api",
        "ScanType": "IacScan",
        "Reporturl": report,
        "RepoUrl": bitbucketRepo,
        "RepoName": repo_path,
        "BranchName": branch,
        "Metadata": Metadata_dict
    }

    try:
        post_helper.send_scan_results(signature)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Failed to send scan results to signature store on {SIGNATURE_STORE_ENDPOINT}")

    return {"Reporturl": report}

@app.get("/v1/ConImgScan")
async def container_image_scan_v1(
    containerRepoUrl: str,
    tool: str,
    Metadata: Optional[str] = Query(None)
):
    if tool.lower() not in SUPPORTED_TOOLS:
        raise HTTPException(status_code=400, detail="Tool not supported. Please use 'wiz' or 'nexus'.")

    try:
        Metadata_dict = json.loads(Metadata) if Metadata else {}
        if not isinstance(Metadata_dict, dict):
            raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")

    image_tar_file_name = crane_helper.pull_container_image(image_url=containerRepoUrl)
    if image_tar_file_name == "Image Pull Failed":
        raise HTTPException(status_code=424, detail="Image pull failed")

    report = wiz_helper.wiz_container_image_scan(image_tarFile_name=image_tar_file_name)

    signature = {
        "ScanSource": "ssdlc-scan-api",
        "ScanType": "ContainerImageScan",
        "Reporturl": report,
        "ContainerImage": containerRepoUrl,
        "Metadata": Metadata_dict
    }

    try:
        post_helper.send_scan_results(signature)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Failed to send scan results to signature store on {SIGNATURE_STORE_ENDPOINT}")

    return {"Reporturl": report}

@app.get("/v1/SCAScan")
async def sca_scan_v1(
    bitbucketRepo: AnyUrl,
    branch: str = "develop",
    Metadata: Optional[str] = Query(None)
):
    try:
        Metadata_dict = json.loads(Metadata) if Metadata else {}
        if not isinstance(Metadata_dict, dict):
            raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"Invalid Metadata format: {Metadata}")

    repo_path = bitbucketRepo.split("/")[-1].replace(".git", "")
    scan_result = nexus_iq_scanner.perform_sca_scan(repository_url=bitbucketRepo, branch=branch)

    signature = {
        "ScanSource": "ssdlc-scan-api",
        "ScanType": "SCAScan",
        "Reporturl": scan_result,
        "RepoUrl": bitbucketRepo,
        "RepoName": repo_path,
        "BranchName": branch,
        "Metadata": Metadata_dict
    }

    try:
        post_helper.send_scan_results(signature)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Failed to send scan results to signature store on {SIGNATURE_STORE_ENDPOINT}")

    return {"Reporturl": scan_result}

@app.get("/v1/staticCodeScan")
async def static_code_scan_v1(
    bitbucketRepo: AnyUrl,
    branch: str = "develop",
    pathToScan: str = ".",
    commit_id: Optional[str] = None,
    Metadata: Optional[str] = Query(None)
):
    try:
        Metadata_dict = json.loads(Metadata) if Metadata else {}
        if not isinstance(Metadata_dict, dict):
            raise HTTPException(status_code=422, detail="Invalid Metadata format")
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid Metadata format")

    repo_path = bitbucketRepo.split("/")[-1].replace(".git", "")
    scan_result = sonarqube_scanner.perform_sonarqube_scan(
        repository_url=bitbucketRepo,
        branch=branch,
        path_to_scan=pathToScan,
        commit_id=commit_id
    )

    signature = {
        "ScanSource": "ssdlc-scan-api",
        "ScanType": "staticCodeScan",
        "Reporturl": scan_result,
        "RepoUrl": bitbucketRepo,
        "RepoName": repo_path,
        "BranchName": branch,
        "Metadata": Metadata_dict
    }

    try:
        post_helper.send_scan_results(signature)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Failed to send scan results to signature store on {SIGNATURE_STORE_ENDPOINT}")

    return {"Reporturl": scan_result}
