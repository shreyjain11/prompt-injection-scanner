"""
Configuration manager for the prompt injection scanner.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import os


class ConfigManager:
    """Manages configuration for the scanner."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (default: config.yaml in project root)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return self._merge_with_defaults(config)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'scanner': {
                'max_file_size_mb': 10,
                'parallel_workers': 4,
                'use_cache': True,
                'cache_ttl_hours': 1,
                'verbose': False
            },
            'filters': {
                'exclude_patterns': [
                    "node_modules/**",
                    "dist/**",
                    "build/**",
                    "__pycache__/**",
                    ".git/**",
                    "*.min.js",
                    "*.min.css",
                    "*.pyc",
                    "*.pyo",
                    ".DS_Store",
                    "Thumbs.db"
                ],
                'include_patterns': [],
                'max_file_size_mb': 10,
                'skip_binary_files': True
            },
            'rules': {
                'enable_categories': [
                    "direct_injection",
                    "system_pollution", 
                    "template_injection",
                    "unsafe_formatting",
                    "hardcoded_prompts"
                ],
                'language_rules': {
                    'python': {'enabled': True, 'custom_patterns': [], 'severity_overrides': {}},
                    'javascript': {'enabled': True, 'custom_patterns': [], 'severity_overrides': {}},
                    'typescript': {'enabled': True, 'custom_patterns': [], 'severity_overrides': {}},
                    'java': {'enabled': True, 'custom_patterns': [], 'severity_overrides': {}},
                    'go': {'enabled': True, 'custom_patterns': [], 'severity_overrides': {}}
                }
            },
            'severity': {
                'critical': {'color': 'red', 'description': 'Critical vulnerabilities', 'enabled': True},
                'high': {'color': 'bright_red', 'description': 'High-risk vulnerabilities', 'enabled': True},
                'medium': {'color': 'yellow', 'description': 'Medium-risk vulnerabilities', 'enabled': True},
                'low': {'color': 'blue', 'description': 'Low-risk findings', 'enabled': True},
                'info': {'color': 'cyan', 'description': 'Informational findings', 'enabled': True}
            },
            'context_analysis': {
                'enabled': True,
                'safe_contexts': ['print statements', 'logging', 'debug statements', 'comments', 'docstrings'],
                'dangerous_contexts': ['openai api calls', 'langchain calls', 'anthropic api calls', 'cohere api calls', 'http requests']
            },
            'reporting': {
                'output_formats': ['cli', 'json', 'html', 'sarif'],
                'cli': {
                    'show_confidence': True,
                    'show_context': True,
                    'color_output': True,
                    'progress_bars': True
                },
                'html': {
                    'template_path': 'templates/report.html',
                    'include_code_snippets': True,
                    'include_recommendations': True
                },
                'sarif': {
                    'include_help_uri': True,
                    'include_rule_help': True
                }
            },
            'performance': {
                'enable_ast_analysis': True,
                'enable_context_analysis': True,
                'enable_caching': True,
                'cache_directory': '~/.prompt-scanner/cache',
                'memory_optimization': {
                    'streaming_processing': False,
                    'chunk_size_mb': 1,
                    'max_memory_mb': 512
                }
            },
            'custom_rules': []
        }
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults."""
        default_config = self._get_default_config()
        return self._deep_merge(default_config, config)
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_scanner_config(self) -> Dict[str, Any]:
        """Get scanner configuration."""
        return self.config.get('scanner', {})
    
    def get_filter_config(self) -> Dict[str, Any]:
        """Get filter configuration."""
        return self.config.get('filters', {})
    
    def get_rules_config(self) -> Dict[str, Any]:
        """Get rules configuration."""
        return self.config.get('rules', {})
    
    def get_severity_config(self) -> Dict[str, Any]:
        """Get severity configuration."""
        return self.config.get('severity', {})
    
    def get_context_analysis_config(self) -> Dict[str, Any]:
        """Get context analysis configuration."""
        return self.config.get('context_analysis', {})
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """Get reporting configuration."""
        return self.config.get('reporting', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get('performance', {})
    
    def get_custom_rules(self) -> List[Dict[str, Any]]:
        """Get custom rules."""
        return self.config.get('custom_rules', [])
    
    def is_rule_enabled(self, rule_category: str) -> bool:
        """Check if a rule category is enabled."""
        enabled_categories = self.get('rules.enable_categories', [])
        return rule_category in enabled_categories
    
    def is_language_enabled(self, language: str) -> bool:
        """Check if a language is enabled."""
        language_rules = self.get('rules.language_rules', {})
        if language in language_rules:
            return language_rules[language].get('enabled', True)
        return True
    
    def is_severity_enabled(self, severity: str) -> bool:
        """Check if a severity level is enabled."""
        severity_config = self.get('severity', {})
        if severity in severity_config:
            return severity_config[severity].get('enabled', True)
        return True
    
    def get_exclude_patterns(self) -> List[str]:
        """Get exclude patterns."""
        return self.get('filters.exclude_patterns', [])
    
    def get_include_patterns(self) -> List[str]:
        """Get include patterns."""
        return self.get('filters.include_patterns', [])
    
    def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB."""
        return self.get('filters.max_file_size_mb', 10)
    
    def should_skip_binary_files(self) -> bool:
        """Check if binary files should be skipped."""
        return self.get('filters.skip_binary_files', True)
    
    def get_parallel_workers(self) -> int:
        """Get number of parallel workers."""
        return self.get('scanner.parallel_workers', 4)
    
    def should_use_cache(self) -> bool:
        """Check if caching should be used."""
        return self.get('scanner.use_cache', True)
    
    def get_cache_ttl_hours(self) -> int:
        """Get cache TTL in hours."""
        return self.get('scanner.cache_ttl_hours', 1)
    
    def is_verbose(self) -> bool:
        """Check if verbose mode is enabled."""
        return self.get('scanner.verbose', False)
    
    def is_context_analysis_enabled(self) -> bool:
        """Check if context analysis is enabled."""
        return self.get('context_analysis.enabled', True)
    
    def is_ast_analysis_enabled(self) -> bool:
        """Check if AST analysis is enabled."""
        return self.get('performance.enable_ast_analysis', True)
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()





