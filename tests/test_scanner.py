"""
Basic tests for the prompt injection scanner.
"""

import pytest
from pathlib import Path
from src.scanner.core import PromptScanner
from src.config.manager import ConfigManager
from src.rules.loader import RuleLoader


class TestScanner:
    """Test the main scanner functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = ConfigManager()
        self.scanner = PromptScanner(config=self.config)
        self.test_dir = Path(__file__).parent / "test_files"
        self.test_dir.mkdir(exist_ok=True)
    
    def test_scanner_initialization(self):
        """Test scanner initialization."""
        assert self.scanner is not None
        assert self.scanner.config is not None
        assert self.scanner.file_processor is not None
        assert self.scanner.rule_engine is not None
    
    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        results = self.scanner.scan(tmp_path)
        assert results is not None
        assert 'results' in results
        assert 'summary' in results
        assert results['summary'].total_files == 0
        assert results['summary'].total_findings == 0
    
    def test_scan_with_vulnerable_file(self, tmp_path):
        """Test scanning a file with known vulnerabilities."""
        # Create a test file with vulnerabilities
        test_file = tmp_path / "vulnerable.py"
        test_content = '''
import openai

def vulnerable_function(user_input):
    prompt = "You are a helpful assistant. " + user_input
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def safe_function(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return response.choices[0].message.content
'''
        test_file.write_text(test_content)
        
        # Scan the directory
        results = self.scanner.scan(tmp_path)
        
        # Verify results
        assert results['summary'].total_files == 1
        assert results['summary'].total_findings > 0
        
        # Check that vulnerabilities were found
        findings = []
        for result in results['results']:
            findings.extend(result.findings)
        
        # Should find at least one vulnerability
        assert len(findings) > 0
        
        # Check that high confidence findings exist
        high_confidence_findings = [f for f in findings if f.get('confidence', 0) > 0.5]
        assert len(high_confidence_findings) > 0
    
    def test_scan_with_safe_file(self, tmp_path):
        """Test scanning a file with safe patterns."""
        # Create a test file with safe patterns
        test_file = tmp_path / "safe.py"
        test_content = '''
def safe_function(user_input):
    print(f"User input: {user_input}")
    return "Safe response"

def another_safe_function():
    logging.info("This is safe logging")
    return "Safe"
'''
        test_file.write_text(test_content)
        
        # Scan the directory
        results = self.scanner.scan(tmp_path)
        
        # Verify results
        assert results['summary'].total_files == 1
        
        # Check findings
        findings = []
        for result in results['results']:
            findings.extend(result.findings)
        
        # Should have low confidence findings for safe patterns
        low_confidence_findings = [f for f in findings if f.get('confidence', 0) < 0.5]
        assert len(low_confidence_findings) > 0
    
    def test_language_detection(self, tmp_path):
        """Test language detection."""
        # Create files in different languages
        python_file = tmp_path / "test.py"
        js_file = tmp_path / "test.js"
        
        python_file.write_text("print('Hello, World!')")
        js_file.write_text("console.log('Hello, World!');")
        
        # Scan the directory
        results = self.scanner.scan(tmp_path)
        
        # Verify that both files were detected
        assert results['summary'].total_files == 2
        
        # Check that languages were detected
        languages = set()
        for result in results['results']:
            if result.language:
                languages.add(result.language)
        
        assert 'python' in languages
        assert 'javascript' in languages
    
    def test_exclude_patterns(self, tmp_path):
        """Test exclude patterns functionality."""
        # Create files that should be excluded
        excluded_dir = tmp_path / "node_modules"
        excluded_dir.mkdir()
        excluded_file = excluded_dir / "package.json"
        excluded_file.write_text('{"name": "test"}')
        
        # Create a file that should be scanned
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello')")
        
        # Scan with exclude patterns
        scanner = PromptScanner(exclude_patterns=["node_modules/**"])
        results = scanner.scan(tmp_path)
        
        # Should only scan the Python file, not the node_modules
        assert results['summary'].total_files == 1
    
    def test_parallel_scanning(self, tmp_path):
        """Test parallel scanning functionality."""
        # Create multiple test files
        for i in range(5):
            test_file = tmp_path / f"test_{i}.py"
            test_file.write_text(f"print('Test {i}')")
        
        # Scan with parallel workers
        scanner = PromptScanner(parallel_workers=2)
        results = scanner.scan(tmp_path)
        
        # Should scan all files
        assert results['summary'].total_files == 5
    
    def test_caching(self, tmp_path):
        """Test caching functionality."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello')")
        
        # First scan
        scanner = PromptScanner(use_cache=True)
        results1 = scanner.scan(tmp_path)
        
        # Second scan (should use cache)
        results2 = scanner.scan(tmp_path)
        
        # Results should be the same
        assert results1['summary'].total_files == results2['summary'].total_files
        assert results1['summary'].total_findings == results2['summary'].total_findings
    
    def test_no_cache(self, tmp_path):
        """Test scanning without cache."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('Hello')")
        
        # Scan without cache
        scanner = PromptScanner(use_cache=False)
        results = scanner.scan(tmp_path)
        
        # Should still work
        assert results['summary'].total_files == 1


class TestConfigManager:
    """Test the configuration manager."""
    
    def test_default_config(self):
        """Test default configuration loading."""
        config = ConfigManager()
        assert config is not None
        assert config.get('scanner.parallel_workers') == 4
        assert config.get('scanner.use_cache') is True
    
    def test_config_getters(self):
        """Test configuration getter methods."""
        config = ConfigManager()
        
        # Test various getters
        assert config.get_parallel_workers() == 4
        assert config.should_use_cache() is True
        assert config.is_verbose() is False
        assert config.get_max_file_size_mb() == 10
    
    def test_exclude_patterns(self):
        """Test exclude patterns configuration."""
        config = ConfigManager()
        patterns = config.get_exclude_patterns()
        
        assert isinstance(patterns, list)
        assert "node_modules/**" in patterns
        assert "dist/**" in patterns


class TestRuleLoader:
    """Test the rule loader."""
    
    def test_rule_loading(self):
        """Test rule loading functionality."""
        loader = RuleLoader()
        assert loader is not None
        
        # Check that rules were loaded
        languages = loader.get_supported_languages()
        assert len(languages) > 0
        
        # Check statistics
        stats = loader.get_rule_statistics()
        assert stats['total_languages'] > 0
        assert stats['total_rules'] > 0
    
    def test_rule_validation(self):
        """Test rule validation."""
        loader = RuleLoader()
        errors = loader.validate_rules()
        
        # Should not have validation errors
        assert len(errors) == 0
    
    def test_get_rules_for_language(self):
        """Test getting rules for a specific language."""
        loader = RuleLoader()
        
        # Test Python rules
        python_rules = loader.get_rules_for_language('python')
        assert len(python_rules) > 0
        
        # Test JavaScript rules
        js_rules = loader.get_rules_for_language('javascript')
        assert len(js_rules) > 0
    
    def test_get_rule_by_id(self):
        """Test getting a specific rule by ID."""
        loader = RuleLoader()
        
        # Test getting a rule by ID
        rule = loader.get_rule_by_id('PI-PY-001')
        assert rule is not None
        assert rule.id == 'PI-PY-001'
        assert rule.severity == 'high'


if __name__ == "__main__":
    pytest.main([__file__])







