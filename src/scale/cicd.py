"""
SafeAI CodeGuard Protocol - CI/CD Integration
Implements CI/CD pipeline integration and automation.
"""

import os
import asyncio
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime
import yaml
import aiohttp
from pathlib import Path
import json

@dataclass
class PipelineStep:
    """Represents a CI/CD pipeline step"""
    name: str
    command: str
    environment: Dict[str, str] = field(default_factory=dict)
    timeout: int = 3600  # 1 hour default
    retry: int = 0
    metadata: Dict = field(default_factory=dict)

@dataclass
class Pipeline:
    """Represents a CI/CD pipeline"""
    name: str
    steps: List[PipelineStep]
    triggers: List[str]
    environment: Dict[str, str] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

class CICDManager:
    """Manages CI/CD integration"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.pipelines: Dict[str, Pipeline] = {}
    
    def load_pipeline(self, pipeline_file: str) -> Pipeline:
        """Load pipeline configuration from YAML"""
        config_path = self.config_dir / pipeline_file
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        steps = []
        for step_config in config["steps"]:
            step = PipelineStep(
                name=step_config["name"],
                command=step_config["command"],
                environment=step_config.get("environment", {}),
                timeout=step_config.get("timeout", 3600),
                retry=step_config.get("retry", 0),
                metadata=step_config.get("metadata", {})
            )
            steps.append(step)
        
        pipeline = Pipeline(
            name=config["name"],
            steps=steps,
            triggers=config.get("triggers", []),
            environment=config.get("environment", {}),
            metadata=config.get("metadata", {})
        )
        
        self.pipelines[pipeline.name] = pipeline
        return pipeline
    
    def generate_github_workflow(
        self,
        pipeline: Pipeline,
        output_file: str
    ):
        """Generate GitHub Actions workflow"""
        workflow = {
            "name": pipeline.name,
            "on": {
                trigger: {} for trigger in pipeline.triggers
            },
            "jobs": {
                "validate": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v2"
                        }
                    ]
                }
            }
        }
        
        # Add pipeline steps
        for step in pipeline.steps:
            workflow["jobs"]["validate"]["steps"].append({
                "name": step.name,
                "run": step.command,
                "env": {**pipeline.environment, **step.environment},
                "timeout-minutes": step.timeout // 60
            })
        
        # Write workflow file
        workflow_path = self.config_dir / output_file
        with open(workflow_path, "w") as f:
            yaml.safe_dump(workflow, f)
    
    def generate_gitlab_ci(
        self,
        pipeline: Pipeline,
        output_file: str
    ):
        """Generate GitLab CI configuration"""
        config = {
            "stages": ["validate"],
            "variables": pipeline.environment
        }
        
        # Add pipeline steps
        for step in pipeline.steps:
            config[f"validate_{step.name}"] = {
                "stage": "validate",
                "script": [step.command],
                "variables": step.environment,
                "timeout": step.timeout,
                "retry": {
                    "max": step.retry
                } if step.retry > 0 else None
            }
        
        # Write config file
        config_path = self.config_dir / output_file
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)

class GitHubIntegration:
    """GitHub-specific CI/CD integration"""
    
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str
    ):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.session = None
    
    async def connect(self):
        """Create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    async def create_check_run(
        self,
        name: str,
        head_sha: str,
        status: str = "in_progress",
        conclusion: Optional[str] = None,
        output: Optional[Dict] = None
    ) -> Dict:
        """Create a check run"""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/check-runs"
        payload = {
            "name": name,
            "head_sha": head_sha,
            "status": status
        }
        
        if conclusion:
            payload["conclusion"] = conclusion
        if output:
            payload["output"] = output
        
        async with self.session.post(url, json=payload) as response:
            return await response.json()
    
    async def update_check_run(
        self,
        check_run_id: int,
        status: str,
        conclusion: Optional[str] = None,
        output: Optional[Dict] = None
    ) -> Dict:
        """Update a check run"""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/check-runs/{check_run_id}"
        payload = {"status": status}
        
        if conclusion:
            payload["conclusion"] = conclusion
        if output:
            payload["output"] = output
        
        async with self.session.patch(url, json=payload) as response:
            return await response.json()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

class GitLabIntegration:
    """GitLab-specific CI/CD integration"""
    
    def __init__(
        self,
        token: str,
        project_id: Union[str, int],
        base_url: str = "https://gitlab.com/api/v4"
    ):
        self.token = token
        self.project_id = project_id
        self.base_url = base_url
        self.session = None
    
    async def connect(self):
        """Create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "PRIVATE-TOKEN": self.token
            })
    
    async def create_pipeline(
        self,
        ref: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict:
        """Create a pipeline"""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/projects/{self.project_id}/pipeline"
        payload = {"ref": ref}
        
        if variables:
            payload["variables"] = [
                {"key": k, "value": v}
                for k, v in variables.items()
            ]
        
        async with self.session.post(url, json=payload) as response:
            return await response.json()
    
    async def get_pipeline_status(
        self,
        pipeline_id: int
    ) -> Dict:
        """Get pipeline status"""
        if not self.session:
            await self.connect()
        
        url = f"{self.base_url}/projects/{self.project_id}/pipelines/{pipeline_id}"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
