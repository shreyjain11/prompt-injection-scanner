"""
Rule loader for YAML-based vulnerability detection rules.
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class RulePattern:
    """Represents a single rule pattern."""
    pattern: str
    message: str
    compiled: re.Pattern


@dataclass
class Rule:
    """Represents a single rule."""
    id: str
    name: str
    description: str
    severity: str
    patterns: List[RulePattern]
    examples: Dict[str, List[str]]


@dataclass
class RuleSet:
    """Represents a complete rule set for a language."""
    language: str
    version: str
    description: str
    rules: Dict[str, List[Rule]]
    context_analysis: Dict[str, List[str]]
    frameworks: List[Dict[str, Any]]


class RuleLoader:
    """Loads and manages YAML-based vulnerability detection rules."""
    
    def __init__(self, rules_dir: Optional[Path] = None):
        """
        Initialize the rule loader.
        
        Args:
            rules_dir: Directory containing rule files (default: rules/ in project root)
        """
        if rules_dir is None:
            # Prefer packaged rules_data, fallback to repo /rules
            pkg_rules = Path(__file__).parent.parent / "rules_data"
            if pkg_rules.exists():
                rules_dir = pkg_rules
            else:
                rules_dir = Path(__file__).parent.parent.parent / "rules"
        
        self.rules_dir = rules_dir
        self.rule_sets: Dict[str, RuleSet] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load all rule files from the rules directory."""
        if not self.rules_dir.exists():
            print(f"Warning: Rules directory {self.rules_dir} does not exist")
            return
        
        for rule_file in self.rules_dir.glob("*.yaml"):
            try:
                rule_set = self._load_rule_file(rule_file)
                if rule_set:
                    self.rule_sets[rule_set.language] = rule_set
            except Exception as e:
                print(f"Warning: Could not load rule file {rule_file}: {e}")
    
    def _load_rule_file(self, rule_file: Path) -> Optional[RuleSet]:
        """Load a single rule file."""
        with open(rule_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return None
        
        # Extract basic information
        language = data.get('language', 'unknown')
        version = data.get('version', '1.0')
        description = data.get('description', '')
        
        # Load rules
        rules = {}
        for category, rule_list in data.get('rules', {}).items():
            rules[category] = []
            for rule_data in rule_list:
                rule = self._create_rule(rule_data)
                if rule:
                    rules[category].append(rule)
        
        # Load context analysis
        context_analysis = data.get('context_analysis', {})
        
        # Load frameworks
        frameworks = data.get('frameworks', [])
        
        return RuleSet(
            language=language,
            version=version,
            description=description,
            rules=rules,
            context_analysis=context_analysis,
            frameworks=frameworks
        )
    
    def _create_rule(self, rule_data: Dict[str, Any]) -> Optional[Rule]:
        """Create a Rule object from rule data."""
        rule_id = rule_data.get('id')
        name = rule_data.get('name')
        description = rule_data.get('description')
        severity = rule_data.get('severity', 'medium')
        
        if not all([rule_id, name, description]):
            return None
        
        # Create patterns
        patterns = []
        for pattern_data in rule_data.get('patterns', []):
            pattern_str = pattern_data.get('pattern')
            message = pattern_data.get('message', '')
            
            if pattern_str:
                try:
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    patterns.append(RulePattern(
                        pattern=pattern_str,
                        message=message,
                        compiled=compiled_pattern
                    ))
                except re.error as e:
                    print(f"Warning: Invalid regex pattern in rule {rule_id}: {e}")
        
        # Get examples
        examples = rule_data.get('examples', {})
        
        return Rule(
            id=rule_id,
            name=name,
            description=description,
            severity=severity,
            patterns=patterns,
            examples=examples
        )
    
    def get_rule_set(self, language: str) -> Optional[RuleSet]:
        """Get rule set for a specific language."""
        return self.rule_sets.get(language)
    
    def get_rules_for_language(self, language: str, category: Optional[str] = None) -> List[Rule]:
        """Get rules for a specific language and optionally category."""
        rule_set = self.get_rule_set(language)
        if not rule_set:
            return []
        
        if category:
            return rule_set.rules.get(category, [])
        
        # Return all rules
        all_rules = []
        for rules in rule_set.rules.values():
            all_rules.extend(rules)
        return all_rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        for rule_set in self.rule_sets.values():
            for rules in rule_set.rules.values():
                for rule in rules:
                    if rule.id == rule_id:
                        return rule
        return None
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.rule_sets.keys())
    
    def get_rule_categories(self, language: str) -> List[str]:
        """Get rule categories for a language."""
        rule_set = self.get_rule_set(language)
        if rule_set:
            return list(rule_set.rules.keys())
        return []
    
    def reload_rules(self):
        """Reload all rules from files."""
        self.rule_sets.clear()
        self._load_rules()
    
    def validate_rules(self) -> List[str]:
        """Validate all loaded rules and return any errors."""
        errors = []
        
        for language, rule_set in self.rule_sets.items():
            for category, rules in rule_set.rules.items():
                for rule in rules:
                    # Check for duplicate rule IDs
                    if self._has_duplicate_rule_id(rule.id, language, category):
                        errors.append(f"Duplicate rule ID {rule.id} in {language}/{category}")
                    
                    # Validate patterns
                    for pattern in rule.patterns:
                        try:
                            re.compile(pattern.pattern)
                        except re.error as e:
                            errors.append(f"Invalid pattern in rule {rule.id}: {e}")
        
        return errors
    
    def _has_duplicate_rule_id(self, rule_id: str, language: str, category: str) -> bool:
        """Check if a rule ID is duplicated."""
        count = 0
        for lang, rule_set in self.rule_sets.items():
            for cat, rules in rule_set.rules.items():
                for rule in rules:
                    if rule.id == rule_id:
                        count += 1
                        if count > 1:
                            return True
        return False
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        stats = {
            'total_languages': len(self.rule_sets),
            'languages': {},
            'total_rules': 0,
            'rules_by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        }
        
        for language, rule_set in self.rule_sets.items():
            language_stats = {
                'categories': len(rule_set.rules),
                'total_rules': 0,
                'rules_by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            }
            
            for rules in rule_set.rules.values():
                language_stats['total_rules'] += len(rules)
                stats['total_rules'] += len(rules)
                
                for rule in rules:
                    severity = rule.severity.lower()
                    if severity in language_stats['rules_by_severity']:
                        language_stats['rules_by_severity'][severity] += 1
                    if severity in stats['rules_by_severity']:
                        stats['rules_by_severity'][severity] += 1
            
            stats['languages'][language] = language_stats
        
        return stats




