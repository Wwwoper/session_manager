"""
Tests for integrations/git.py
"""

from unittest.mock import Mock, patch
import subprocess

from session_manager.integrations.git import GitIntegration


class TestGitIntegrationInit:
    """Test GitIntegration initialization"""
    
    def test_init(self, tmp_path):
        """Test basic initialization"""
        git = GitIntegration(tmp_path)
        
        assert git.project_path == tmp_path.resolve()
        assert git._git_available is None
        assert git._is_repo is None


class TestGitAvailability:
    """Test git availability checking"""
    
    def test_is_git_available_true(self, tmp_path):
        """Test when git is available"""
        git = GitIntegration(tmp_path)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            result = git.is_git_available()
            
            assert result is True
            assert git._git_available is True
    
    def test_is_git_available_false(self, tmp_path):
        """Test when git is not available"""
        git = GitIntegration(tmp_path)
        
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = git.is_git_available()
            
            assert result is False
            assert git._git_available is False
    
    def test_is_git_available_cached(self, tmp_path):
        """Test that availability is cached"""
        git = GitIntegration(tmp_path)
        git._git_available = True
        
        # Should not call subprocess
        result = git.is_git_available()
        
        assert result is True


class TestGitRepo:
    """Test git repository detection"""
    
    def test_is_git_repo_true(self, tmp_path):
        """Test when directory is a git repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = git.is_git_repo()
                
                assert result is True
    
    def test_is_git_repo_false(self, tmp_path):
        """Test when directory is not a git repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_available', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=1)
                
                result = git.is_git_repo()
                
                assert result is False
    
    def test_is_git_repo_no_git(self, tmp_path):
        """Test when git is not available"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_available', return_value=False):
            result = git.is_git_repo()
            
            assert result is False


class TestGitBranch:
    """Test git branch operations"""
    
    def test_get_current_branch(self, tmp_path):
        """Test getting current branch"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="main\n"
                )
                
                branch = git.get_current_branch()
                
                assert branch == "main"
    
    def test_get_current_branch_not_repo(self, tmp_path):
        """Test getting branch when not a repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=False):
            branch = git.get_current_branch()
            
            assert branch is None
    
    def test_get_current_branch_error(self, tmp_path):
        """Test getting branch with error"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run', side_effect=subprocess.SubprocessError):
                branch = git.get_current_branch()
                
                assert branch is None


class TestGitCommit:
    """Test git commit operations"""
    
    def test_get_last_commit(self, tmp_path):
        """Test getting last commit"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="abc123 Initial commit\n"
                )
                
                commit = git.get_last_commit()
                
                assert commit == "abc123 Initial commit"
    
    def test_get_last_commit_not_repo(self, tmp_path):
        """Test getting commit when not a repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=False):
            commit = git.get_last_commit()
            
            assert commit is None


class TestGitStatus:
    """Test git status operations"""
    
    def test_get_uncommitted_changes(self, tmp_path):
        """Test getting uncommitted changes"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="M file1.py\n?? file2.py\n"
                )
                
                changes = git.get_uncommitted_changes()
                
                assert "M file1.py" in changes
                assert "?? file2.py" in changes
    
    def test_get_uncommitted_changes_none(self, tmp_path):
        """Test when no uncommitted changes"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout=""
                )
                
                changes = git.get_uncommitted_changes()
                
                assert changes is None
    
    def test_has_uncommitted_changes_true(self, tmp_path):
        """Test has_uncommitted_changes when true"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'get_uncommitted_changes', return_value="M file.py"):
            result = git.has_uncommitted_changes()
            
            assert result is True
    
    def test_has_uncommitted_changes_false(self, tmp_path):
        """Test has_uncommitted_changes when false"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'get_uncommitted_changes', return_value=None):
            result = git.has_uncommitted_changes()
            
            assert result is False


class TestGitOperations:
    """Test git operations (add, commit)"""
    
    def test_add_all_success(self, tmp_path):
        """Test adding all files"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = git.add_all()
                
                assert result is True
    
    def test_add_all_not_repo(self, tmp_path):
        """Test add_all when not a repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=False):
            result = git.add_all()
            
            assert result is False
    
    def test_create_commit_success(self, tmp_path):
        """Test creating a commit"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0)
                
                result = git.create_commit("Test commit")
                
                assert result is True
    
    def test_create_commit_empty_message(self, tmp_path):
        """Test creating commit with empty message"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            result = git.create_commit("")
            
            assert result is False
    
    def test_create_commit_not_repo(self, tmp_path):
        """Test creating commit when not a repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=False):
            result = git.create_commit("Test")
            
            assert result is False


class TestGitRemote:
    """Test git remote operations"""
    
    def test_get_remote_url(self, tmp_path):
        """Test getting remote URL"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(
                    returncode=0,
                    stdout="https://github.com/user/repo.git\n"
                )
                
                url = git.get_remote_url()
                
                assert url == "https://github.com/user/repo.git"
    
    def test_get_remote_url_not_repo(self, tmp_path):
        """Test getting remote URL when not a repo"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=False):
            url = git.get_remote_url()
            
            assert url is None


class TestGitInfo:
    """Test getting all git info"""
    
    def test_get_git_info(self, tmp_path):
        """Test getting all git information"""
        git = GitIntegration(tmp_path)
        
        with patch.object(git, 'is_git_repo', return_value=True):
            with patch.object(git, 'get_current_branch', return_value="main"):
                with patch.object(git, 'get_last_commit', return_value="abc123 Commit"):
                    with patch.object(git, 'get_uncommitted_changes', return_value="M file.py"):
                        with patch.object(git, 'get_remote_url', return_value="https://github.com/user/repo"):
                            
                            info = git.get_git_info()
                            
                            assert info["is_repo"] is True
                            assert info["branch"] == "main"
                            assert info["last_commit"] == "abc123 Commit"
                            assert info["uncommitted_changes"] == "M file.py"
                            assert info["has_changes"] is True
                            assert info["remote_url"] == "https://github.com/user/repo"