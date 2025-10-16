"""
Tests for integrations/tests.py
"""

import subprocess
from unittest.mock import Mock, patch

from session_manager.integrations.tests import TestsIntegration


class TestTestsIntegrationInit:
    """Test TestsIntegration initialization"""
    
    def test_init(self, tmp_path):
        """Test basic initialization"""
        tests = TestsIntegration(tmp_path)
        
        assert tests.project_path == tmp_path.resolve()
        assert tests._pytest_available is None


class TestPytestAvailability:
    """Test pytest availability checking"""
    
    def test_is_pytest_available_true(self, tmp_path):
        """Test when pytest is available"""
        tests = TestsIntegration(tmp_path)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = tests.is_pytest_available()
            
            assert result is True
    
    def test_is_pytest_available_false(self, tmp_path):
        """Test when pytest is not available"""
        tests = TestsIntegration(tmp_path)
        
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = tests.is_pytest_available()
            
            assert result is False
    
    def test_is_pytest_available_cached(self, tmp_path):
        """Test that availability is cached"""
        tests = TestsIntegration(tmp_path)
        tests._pytest_available = True
        
        result = tests.is_pytest_available()
        
        assert result is True


class TestHasTests:
    """Test test file detection"""
    
    def test_has_tests_true(self, tmp_path):
        """Test when test files exist"""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").touch()
        
        tests = TestsIntegration(tmp_path)
        
        result = tests.has_tests()
        
        assert result is True
    
    def test_has_tests_false(self, tmp_path):
        """Test when no test files exist"""
        tests = TestsIntegration(tmp_path)
        
        result = tests.has_tests()
        
        assert result is False
    
    def test_has_tests_different_pattern(self, tmp_path):
        """Test with different test file pattern"""
        (tmp_path / "example_test.py").touch()
        
        tests = TestsIntegration(tmp_path)
        
        result = tests.has_tests()
        
        assert result is True


class TestRunTests:
    """Test running tests"""
    
    def test_run_tests_success(self, tmp_path):
        """Test running tests successfully"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="5 passed\n",
                    stderr=""
                )
                
                result = tests.run_tests()
                
                assert result["success"] is True
                assert result["passed"] == 5
                assert result["failed"] == 0
    
    def test_run_tests_failures(self, tmp_path):
        """Test running tests with failures"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=1,
                    stdout="3 passed, 2 failed\n",
                    stderr=""
                )
                
                result = tests.run_tests()
                
                assert result["success"] is False
                assert result["passed"] == 3
                assert result["failed"] == 2
    
    def test_run_tests_not_available(self, tmp_path):
        """Test running tests when pytest not available"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=False):
            result = tests.run_tests()
            
            assert result["success"] is False
            assert "error" in result
            assert result["passed"] == 0
    
    def test_run_tests_timeout(self, tmp_path):
        """Test running tests with timeout"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                # Simulate timeout
                mock_run.side_effect = subprocess.TimeoutExpired(cmd='pytest', timeout=30)
                
                result = tests.run_tests()
                
                assert result["success"] is False
                assert result["error"] == "timeout"


class TestCollectTests:
    """Test test collection"""
    
    def test_collect_tests(self, tmp_path):
        """Test collecting tests"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="10 tests collected\n"
                )
                
                result = tests.collect_tests()
                
                assert result == "10 tests collected"
    
    def test_collect_tests_not_available(self, tmp_path):
        """Test collecting when pytest not available"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=False):
            result = tests.collect_tests()
            
            assert result is None


class TestTestSummary:
    """Test getting test summary"""
    
    def test_get_test_summary(self, tmp_path):
        """Test getting test summary"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'collect_tests', return_value="5 tests collected"):
            result = tests.get_test_summary()
            
            assert result == "5 tests collected"
    
    def test_get_test_summary_not_available(self, tmp_path):
        """Test summary when pytest not available"""
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=False):
            result = tests.get_test_summary()
            
            assert result is None


class TestParseOutput:
    """Test output parsing"""
    
    def test_parse_test_output_passed(self, tmp_path):
        """Test parsing output with passed tests"""
        tests = TestsIntegration(tmp_path)
        
        output = "test_example.py .... 5 passed in 1.2s"
        passed, failed = tests._parse_test_output(output)
        
        assert passed == 5
        assert failed == 0
    
    def test_parse_test_output_failed(self, tmp_path):
        """Test parsing output with failed tests"""
        tests = TestsIntegration(tmp_path)
        
        output = "test_example.py ..F. 3 passed, 1 failed in 1.2s"
        passed, failed = tests._parse_test_output(output)
        
        assert passed == 3
        assert failed == 1
    
    def test_parse_test_output_none(self, tmp_path):
        """Test parsing output with no test info"""
        tests = TestsIntegration(tmp_path)
        
        output = "No tests found"
        passed, failed = tests._parse_test_output(output)
        
        assert passed == 0
        assert failed == 0


class TestGenerateSummary:
    """Test summary generation"""
    
    def test_generate_summary_all_passed(self, tmp_path):
        """Test summary when all tests pass"""
        tests = TestsIntegration(tmp_path)
        
        summary = tests._generate_summary(5, 0)
        
        assert "5 tests passed" in summary
    
    def test_generate_summary_all_failed(self, tmp_path):
        """Test summary when all tests fail"""
        tests = TestsIntegration(tmp_path)
        
        summary = tests._generate_summary(0, 3)
        
        assert "3 tests failed" in summary
    
    def test_generate_summary_mixed(self, tmp_path):
        """Test summary with mixed results"""
        tests = TestsIntegration(tmp_path)
        
        summary = tests._generate_summary(3, 2)
        
        assert "3 passed" in summary
        assert "2 failed" in summary
    
    def test_generate_summary_no_tests(self, tmp_path):
        """Test summary when no tests"""
        tests = TestsIntegration(tmp_path)
        
        summary = tests._generate_summary(0, 0)
        
        assert "No tests" in summary


class TestGetTestInfo:
    """Test getting all test info"""
    
    def test_get_test_info(self, tmp_path):
        """Test getting all test information"""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").touch()
        
        tests = TestsIntegration(tmp_path)
        
        with patch.object(tests, 'is_pytest_available', return_value=True):
            with patch.object(tests, 'get_test_summary', return_value="5 tests"):
                
                info = tests.get_test_info()
                
                assert info["pytest_available"] is True
                assert info["has_tests"] is True
                assert info["summary"] == "5 tests"