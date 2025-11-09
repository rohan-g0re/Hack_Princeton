import sys
import subprocess
import uuid
import json
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional
from app.config import settings
from app.models.job import JobState, JobStatus


class DriverJobRunner:
    """Manages background execution of current_code/main.py"""
    
    def __init__(self):
        self.jobs_dir = settings.jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def start_job(self) -> str:
        """
        Launch current_code/main.py as a background process.
        Returns job_id.
        """
        job_id = str(uuid.uuid4())
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # State file
        state_path = job_dir / "state.json"
        stdout_path = job_dir / "stdout.log"
        stderr_path = job_dir / "stderr.log"
        
        # Python executable (use current venv)
        python_exe = sys.executable
        
        # Script to run
        main_script = settings.data_dir_path / "main.py"
        if not main_script.exists():
            raise FileNotFoundError(f"Driver script not found: {main_script}")
        
        # Build command: python main.py --instacart on --ubereats on
        # (non-interactive mode)
        cmd = [
            python_exe,
            "-u",  # Unbuffered output
            str(main_script),
            "--instacart", "on",
            "--ubereats", "on"
        ]
        
        # Platform-specific process creation
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = (
                subprocess.CREATE_NEW_PROCESS_GROUP |
                subprocess.CREATE_NO_WINDOW
            )
        
        # Start process
        with open(stdout_path, "w") as stdout_f, open(stderr_path, "w") as stderr_f:
            process = subprocess.Popen(
                cmd,
                cwd=str(settings.data_dir_path),
                stdout=stdout_f,
                stderr=stderr_f,
                creationflags=creation_flags
            )
        
        # Save initial state
        state = JobState(
            job_id=job_id,
            status="running",
            pid=process.pid,
            started_at=datetime.utcnow()
        )
        self._save_state(state_path, state)
        
        return job_id
    
    def get_status(self, job_id: str) -> Optional[JobState]:
        """Retrieve job state from disk"""
        state_path = self.jobs_dir / job_id / "state.json"
        if not state_path.exists():
            return None
        
        try:
            with open(state_path, "r") as f:
                data = json.load(f)
            return JobState(**data)
        except Exception as e:
            print(f"[ERROR] get_status: {e}")
            return None
    
    def update_status(self, job_id: str, status: JobStatus, error_message: Optional[str] = None):
        """Update job status"""
        state_path = self.jobs_dir / job_id / "state.json"
        state = self.get_status(job_id)
        if not state:
            return
        
        state.status = status
        if status in ("success", "error"):
            state.ended_at = datetime.utcnow()
        if error_message:
            state.error_message = error_message
        
        self._save_state(state_path, state)
    
    def _save_state(self, path: Path, state: JobState):
        """Save state to disk"""
        with open(path, "w") as f:
            json.dump(state.model_dump(mode="json"), f, indent=2, default=str)


# Singleton
driver_runner = DriverJobRunner()

