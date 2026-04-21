"""Probe execution contexts — SSH, local, mock."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ExecuteResult:
    """Result of command execution."""
    stdout: str
    stderr: str
    returncode: int
    
    @property
    def ok(self) -> bool:
        return self.returncode == 0


class ProbeContext:
    """Base context for probe execution."""
    
    def __init__(self, target: str, execute: callable, metadata: dict = None):
        self.target = target
        self.execute = execute
        self.metadata = metadata or {}


class LocalContext(ProbeContext):
    """Local execution context (runs commands on localhost)."""
    
    def __init__(self, metadata: dict = None):
        import subprocess
        
        def local_execute(cmd: str) -> ExecuteResult:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
            )
            return ExecuteResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        
        super().__init__(target="localhost", execute=local_execute, metadata=metadata)


class MockContext(ProbeContext):
    """Mock context for testing with predefined responses."""
    
    def __init__(self, responses: dict[str, ExecuteResult], metadata: dict = None):
        """
        Args:
            responses: Mapping from command string to ExecuteResult
        """
        self._responses = responses
        
        def mock_execute(cmd: str) -> ExecuteResult:
            return self._responses.get(cmd, ExecuteResult("", "Command not found", 1))
        
        super().__init__(target="mock", execute=mock_execute, metadata=metadata)


class SSHContext(ProbeContext):
    """SSH execution context for remote scanning."""
    
    def __init__(self, target: str, metadata: dict = None, ssh_key_path: str = None):
        """
        Args:
            target: SSH target in format "user@host"
            metadata: Additional metadata
            ssh_key_path: Path to SSH private key (optional)
        """
        self.ssh_key_path = ssh_key_path
        
        def ssh_execute(cmd: str) -> ExecuteResult:
            import subprocess
            
            ssh_cmd = ["ssh"]
            if self.ssh_key_path:
                ssh_cmd.extend(["-i", self.ssh_key_path])
            ssh_cmd.extend([target, cmd])
            
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
            )
            return ExecuteResult(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        
        super().__init__(target=target, execute=ssh_execute, metadata=metadata)
