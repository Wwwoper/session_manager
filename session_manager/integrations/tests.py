"""
Pytest integration for Session Manager

Provides test running and status information with graceful degradation.
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict


class TestsIntegration:
    """
    Integration with pytest test framework.
    
    Provides test execution and status information.
    All methods gracefully handle missing pytest.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize tests integration for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self._pytest_available = None
    
    def is_pytest_available(self) -> bool:
        """
        Check if pytest is installed and accessible.
        
        Returns:
            True if pytest is available
        """
        if self._pytest_available is not None:
            return self._pytest_available
        
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                timeout=2,
            )
            self._pytest_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            self._pytest_available = False
        
        return self._pytest_available
    
    def has_tests(self) -> bool:
        """
        Check if project has test files.
        
        Looks for common test directories and files.
        
        Returns:
            True if test files are found
        """
        # Common test patterns
        test_patterns = [
            "test_*.py",
            "*_test.py",
        ]
        
        # Common test directories
        test_dirs = [
            self.project_path / "tests",
            self.project_path / "test",
            self.project_path,
        ]
        
        for test_dir in test_dirs:
            if not test_dir.exists():
                continue
            
            for pattern in test_patterns:
                if list(test_dir.rglob(pattern)):
                    return True
        
        return False
    
    def run_tests(self, timeout: int = 30, verbose: bool = False) -> Dict:
        """
        Run pytest tests.
        
        Args:
            timeout: Maximum time to wait for tests (seconds)
            verbose: If True, include detailed output
            
        Returns:
            Dictionary with test results:
            - success: bool - if tests ran successfully
            - passed: int - number of passed tests
            - failed: int - number of failed tests
            - output: str - test output (if verbose)
            - summary: str - brief summary
        """
        if not self.is_pytest_available():
            return {
                "success": False,
                "error": "pytest not available",
                "passed": 0,
                "failed": 0,
                "summary": "pytest not installed",
            }
        
        try:
            args = ["pytest", "-v" if verbose else "-q", "--tb=short"]
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_path,
            )
            
            output = result.stdout + result.stderr
            
            # Parse output for test counts
            passed, failed = self._parse_test_output(output)
            
            return {
                "success": result.returncode == 0,
                "passed": passed,
                "failed": failed,
                "output": output if verbose else None,
                "summary": self._generate_summary(passed, failed),
                "exit_code": result.returncode,
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "timeout",
                "passed": 0,
                "failed": 0,
                "summary": f"Tests timed out after {timeout}s",
            }
        except (subprocess.SubprocessError, OSError) as e:
            return {
                "success": False,
                "error": str(e),
                "passed": 0,
                "failed": 0,
                "summary": "Failed to run tests",
            }
    
    def collect_tests(self) -> Optional[str]:
        """
        Collect information about available tests without running them.
        
        Returns:
            String with test collection info, or None if not available
        """
        if not self.is_pytest_available():
            return None
        
        try:
            result = subprocess.run(
                ["pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_path,
            )
            
            if result.returncode == 0 or result.returncode == 5:  # 5 = no tests collected
                return result.stdout.strip()
            
        except (subprocess.SubprocessError, OSError):
            pass
        
        return None
    
    def get_test_summary(self) -> Optional[str]:
        """
        Get a brief summary of tests without running them.
        
        Returns:
            Summary string, or None if not available
        """
        if not self.is_pytest_available():
            return None
        
        collection = self.collect_tests()
        if collection:
            # Extract test count from collection
            lines = collection.split('\n')
            for line in lines:
                if 'test' in line.lower() and any(c.isdigit() for c in line):
                    return line.strip()
        
        return "Tests available"
    
    def _parse_test_output(self, output: str) -> tuple[int, int]:
        """
        Parse pytest output to extract test counts.
        
        Args:
            output: Pytest output text
            
        Returns:
            Tuple of (passed, failed) counts
        """
        passed = 0
        failed = 0
        
        # Look for patterns like "5 passed" or "3 failed"
        import re
        
        passed_match = re.search(r'(\d+)\s+passed', output)
        if passed_match:
            passed = int(passed_match.group(1))
        
        failed_match = re.search(r'(\d+)\s+failed', output)
        if failed_match:
            failed = int(failed_match.group(1))
        
        return passed, failed
    
    def _generate_summary(self, passed: int, failed: int) -> str:
        """
        Generate a brief summary of test results.
        
        Args:
            passed: Number of passed tests
            failed: Number of failed tests
            
        Returns:
            Summary string
        """
        total = passed + failed
        
        if total == 0:
            return "No tests found"
        
        if failed == 0:
            return f"✅ All {passed} tests passed"
        elif passed == 0:
            return f"❌ All {failed} tests failed"
        else:
            return f"⚠️  {passed} passed, {failed} failed"
    
    def get_coverage_info(self) -> Optional[Dict]:
        """
        Get test coverage information (requires pytest-cov).
        
        Returns:
            Dictionary with coverage info, or None if not available
        """
        if not self.is_pytest_available():
            return None
        
        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=term-missing", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path,
            )
            
            # Try to parse coverage percentage
            import re
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', result.stdout)
            
            if match:
                return {
                    "available": True,
                    "percentage": int(match.group(1)),
                    "output": result.stdout,
                }
            
        except (subprocess.SubprocessError, OSError):
            pass
        
        return {"available": False}
    
    def get_test_info(self) -> Dict:
        """
        Get all test information in one call.
        
        Returns:
            Dictionary with test information
        """
        return {
            "pytest_available": self.is_pytest_available(),
            "has_tests": self.has_tests(),
            "summary": self.get_test_summary(),
        }