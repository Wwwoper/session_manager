"""
Tests for integrations/github.py
"""

import json
import subprocess
from unittest.mock import Mock, patch

from session_manager.integrations.github import GitHubIntegration


class TestGitHubIntegrationInit:
    """Test GitHubIntegration initialization"""
    
    def test_init(self, tmp_path):
        """Test basic initialization"""
        gh = GitHubIntegration(tmp_path)
        
        assert gh.project_path == tmp_path.resolve()
        assert gh._gh_available is None


class TestGhAvailability:
    """Test gh CLI availability checking"""
    
    def test_is_gh_available_true(self, tmp_path):
        """Test when gh CLI is available"""
        gh = GitHubIntegration(tmp_path)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = gh.is_gh_available()
            
            assert result is True
    
    def test_is_gh_available_false(self, tmp_path):
        """Test when gh CLI is not available"""
        gh = GitHubIntegration(tmp_path)
        
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = gh.is_gh_available()
            
            assert result is False
    
    def test_is_gh_available_cached(self, tmp_path):
        """Test that availability is cached"""
        gh = GitHubIntegration(tmp_path)
        gh._gh_available = True
        
        result = gh.is_gh_available()
        
        assert result is True
    
    def test_is_gh_available_timeout(self, tmp_path):
        """Test when gh CLI times out"""
        gh = GitHubIntegration(tmp_path)
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('gh', 2)):
            result = gh.is_gh_available()
            
            assert result is False


class TestGitHubRepo:
    """Test GitHub repository detection"""
    
    def test_is_github_repo_true(self, tmp_path):
        """Test when project is a GitHub repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = gh.is_github_repo()
                
                assert result is True
    
    def test_is_github_repo_false(self, tmp_path):
        """Test when project is not a GitHub repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=1)
                
                result = gh.is_github_repo()
                
                assert result is False
    
    def test_is_github_repo_no_gh(self, tmp_path):
        """Test when gh CLI is not available"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=False):
            result = gh.is_github_repo()
            
            assert result is False
    
    def test_is_github_repo_error(self, tmp_path):
        """Test when gh CLI throws error"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=True):
            with patch('subprocess.run', side_effect=OSError):
                result = gh.is_github_repo()
                
                assert result is False


class TestGitHubIssues:
    """Test GitHub issues operations"""
    
    def test_get_open_issues(self, tmp_path):
        """Test getting open issues"""
        gh = GitHubIntegration(tmp_path)
        
        issues_data = [
            {"number": 1, "title": "Bug fix", "labels": []},
            {"number": 2, "title": "Feature request", "labels": []},
        ]
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(issues_data)
                )
                
                issues = gh.get_open_issues()
                
                assert len(issues) == 2
                assert issues[0]["number"] == 1
    
    def test_get_open_issues_empty(self, tmp_path):
        """Test getting issues when none exist"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="[]"
                )
                
                issues = gh.get_open_issues()
                
                assert issues == []
    
    def test_get_open_issues_not_repo(self, tmp_path):
        """Test getting issues when not a repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=False):
            issues = gh.get_open_issues()
            
            assert issues is None
    
    def test_get_open_issues_error(self, tmp_path):
        """Test getting issues with error"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run', side_effect=OSError):
                issues = gh.get_open_issues()
                
                assert issues is None
    
    def test_get_open_issues_invalid_json(self, tmp_path):
        """Test getting issues with invalid JSON"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="invalid json"
                )
                
                issues = gh.get_open_issues()
                
                assert issues is None
    
    def test_get_assigned_issues(self, tmp_path):
        """Test getting assigned issues"""
        gh = GitHubIntegration(tmp_path)
        
        issues_data = [
            {"number": 1, "title": "My issue", "labels": []},
        ]
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(issues_data)
                )
                
                issues = gh.get_assigned_issues()
                
                assert len(issues) == 1
                assert issues[0]["number"] == 1
    
    def test_get_assigned_issues_not_repo(self, tmp_path):
        """Test getting assigned issues when not a repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=False):
            issues = gh.get_assigned_issues()
            
            assert issues is None


class TestGitHubPRs:
    """Test GitHub pull requests operations"""
    
    def test_get_open_prs(self, tmp_path):
        """Test getting open pull requests"""
        gh = GitHubIntegration(tmp_path)
        
        prs_data = [
            {"number": 1, "title": "Fix bug", "author": {"login": "user1"}},
            {"number": 2, "title": "Add feature", "author": {"login": "user2"}},
        ]
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(prs_data)
                )
                
                prs = gh.get_open_prs()
                
                assert len(prs) == 2
                assert prs[0]["number"] == 1
    
    def test_get_open_prs_not_repo(self, tmp_path):
        """Test getting PRs when not a repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=False):
            prs = gh.get_open_prs()
            
            assert prs is None
    
    def test_get_open_prs_error(self, tmp_path):
        """Test getting PRs with error"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.SubprocessError):
                prs = gh.get_open_prs()
                
                assert prs is None


class TestGitHubFormatting:
    """Test formatting functions"""
    
    def test_format_issues_summary(self, tmp_path):
        """Test formatting issues summary"""
        gh = GitHubIntegration(tmp_path)
        
        issues = [
            {"number": 1, "title": "Bug fix"},
            {"number": 2, "title": "Feature request"},
        ]
        
        summary = gh.format_issues_summary(issues)
        
        assert "#1" in summary
        assert "Bug fix" in summary
        assert "#2" in summary
    
    def test_format_issues_summary_empty(self, tmp_path):
        """Test formatting when no issues"""
        gh = GitHubIntegration(tmp_path)
        
        summary = gh.format_issues_summary([])
        
        assert "No open issues" in summary
    
    def test_format_issues_summary_none(self, tmp_path):
        """Test formatting when None"""
        gh = GitHubIntegration(tmp_path)
        
        summary = gh.format_issues_summary(None)
        
        assert "No open issues" in summary
    
    def test_format_issues_summary_long_title(self, tmp_path):
        """Test formatting with long title"""
        gh = GitHubIntegration(tmp_path)
        
        issues = [
            {"number": 1, "title": "A" * 100},
        ]
        
        summary = gh.format_issues_summary(issues)
        
        assert "..." in summary
        assert len(summary.split('\n')[0]) < 100
    
    def test_format_prs_summary(self, tmp_path):
        """Test formatting PRs summary"""
        gh = GitHubIntegration(tmp_path)
        
        prs = [
            {"number": 1, "title": "Fix bug", "author": {"login": "user1"}},
        ]
        
        summary = gh.format_prs_summary(prs)
        
        assert "#1" in summary
        assert "Fix bug" in summary
        assert "@user1" in summary
    
    def test_format_prs_summary_empty(self, tmp_path):
        """Test formatting when no PRs"""
        gh = GitHubIntegration(tmp_path)
        
        summary = gh.format_prs_summary([])
        
        assert "No open pull requests" in summary
    
    def test_format_prs_summary_none(self, tmp_path):
        """Test formatting when None"""
        gh = GitHubIntegration(tmp_path)
        
        summary = gh.format_prs_summary(None)
        
        assert "No open pull requests" in summary


class TestGitHubRepoInfo:
    """Test repository information"""
    
    def test_get_repo_info(self, tmp_path):
        """Test getting repository info"""
        gh = GitHubIntegration(tmp_path)
        
        repo_data = {
            "name": "myrepo",
            "owner": {"login": "user"},
            "description": "Test repo",
            "url": "https://github.com/user/myrepo",
            "isPrivate": False,
        }
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=json.dumps(repo_data)
                )
                
                info = gh.get_repo_info()
                
                assert info["name"] == "myrepo"
                assert info["owner"]["login"] == "user"
    
    def test_get_repo_info_not_repo(self, tmp_path):
        """Test getting info when not a repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=False):
            info = gh.get_repo_info()
            
            assert info is None
    
    def test_get_repo_info_error(self, tmp_path):
        """Test getting info with error"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_github_repo', return_value=True):
            with patch('subprocess.run', side_effect=OSError):
                info = gh.get_repo_info()
                
                assert info is None


class TestGitHubInfo:
    """Test getting all GitHub info"""
    
    def test_get_github_info_not_available(self, tmp_path):
        """Test getting info when gh not available"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=False):
            info = gh.get_github_info()
            
            assert info["available"] is False
            assert info["is_repo"] is False
    
    def test_get_github_info_not_repo(self, tmp_path):
        """Test getting info when not a repo"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=True):
            with patch.object(gh, 'is_github_repo', return_value=False):
                info = gh.get_github_info()
                
                assert info["available"] is True
                assert info["is_repo"] is False
    
    def test_get_github_info_full(self, tmp_path):
        """Test getting full GitHub info"""
        gh = GitHubIntegration(tmp_path)
        
        with patch.object(gh, 'is_gh_available', return_value=True):
            with patch.object(gh, 'is_github_repo', return_value=True):
                with patch.object(gh, 'get_open_issues', return_value=[]):
                    with patch.object(gh, 'get_assigned_issues', return_value=[]):
                        with patch.object(gh, 'get_open_prs', return_value=[]):
                            with patch.object(gh, 'get_repo_info', return_value={}):
                                
                                info = gh.get_github_info()
                                
                                assert info["available"] is True
                                assert info["is_repo"] is True
                                assert "open_issues" in info
                                assert "assigned_issues" in info
                                assert "open_prs" in info
                                assert "repo_info" in info