"""
Rule engine for detecting prompt injection vulnerabilities.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .context_analyzer import ContextAnalyzer


@dataclass
class Finding:
    """Represents a single security finding."""
    rule_id: str
    severity: str
    message: str
    line_number: int
    line_content: str
    context: str
    file_path: Path
    language: Optional[str] = None
    confidence: float = 1.0


class RuleEngine:
    """Engine for applying security rules to detect prompt injection vulnerabilities."""
    
    def __init__(self):
        self.rules = self._load_default_rules()
        self._compiled_patterns = {}
        self._compile_patterns()
        self.context_analyzer = ContextAnalyzer()
        # Drop low-confidence findings by default to improve precision
        self.min_confidence_threshold: float = 0.2
        # Per-severity minimum confidence thresholds (used as max(base, per-severity))
        self.per_severity_min_threshold = {
            'critical': 0.2,
            'high': 0.3,
            'medium': 0.5,
            'low': 0.7,
            'info': 0.8,
        }
        # Strict mode raises thresholds and applies extra filters for higher precision
        self.strict: bool = False
    
    def apply_rules(self, content: str, file_path: Path, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Apply all relevant rules to the file content.
        
        Args:
            content: File content to analyze
            file_path: Path to the file
            language: Detected programming language
            
        Returns:
            List of findings as dictionaries
        """
        findings = []
        lines = content.split('\n')
        
        # Apply language-agnostic rules (but only for code-like languages to avoid data files)
        findings.extend(self._apply_generic_rules(content, lines, file_path, language))
        
        # Apply language-specific rules
        if language:
            findings.extend(self._apply_language_specific_rules(content, lines, file_path, language))
        
        # Score findings based on context analysis
        scored_findings = []
        for finding in findings:
            confidence, reason = self.context_analyzer.analyze_context(
                content, file_path, language, finding.line_number, finding.context, finding.severity
            )
            finding.confidence = confidence
            if reason and reason != 'neutral':
                finding.message += f" (Context: {reason})"
            scored_findings.append(finding)
        
        # Post-filters for precision
        base_threshold = self.min_confidence_threshold
        if self.strict:
            base_threshold = max(base_threshold, 0.7)
        filtered_findings = []
        for f in scored_findings:
            sev = (f.severity or 'low').lower()
            sev_threshold = self.per_severity_min_threshold.get(sev, base_threshold)
            threshold = max(base_threshold, sev_threshold)
            if f.confidence < threshold:
                continue
            # Always apply path-based noise suppression unless dangerous context nearby
            suffix = file_path.suffix.lower()
            lines_local = content.split('\n')
            start_line = max(0, f.line_number - 3)
            end_line = min(len(lines_local), f.line_number + 3)
            surrounding = '\n'.join(lines_local[start_line:end_line])
            in_danger = self.context_analyzer._is_in_dangerous_context(surrounding, language or '')
            noisy_dirs = { 'assets', 'asset', 'samples', 'sample', 'iso', 'vm', 'images', 'image', 'imgs', 'img' }
            if any(part.lower() in noisy_dirs for part in file_path.parts):
                if not in_danger:
                    continue
            if self.strict:
                # Strongly filter documentation/data/examples unless clearly dangerous
                suffix = file_path.suffix.lower()
                is_doc = suffix in {'.md', '.markdown', '.txt', '.csv', '.tsv'}
                # Re-check local dangerous context around line
                lines = content.split('\n')
                start_line = max(0, f.line_number - 3)
                end_line = min(len(lines), f.line_number + 3)
                surrounding = '\n'.join(lines[start_line:end_line])
                in_danger = self.context_analyzer._is_in_dangerous_context(surrounding, language or '')
                # If medium severity (e.g., hardcoded prompts), require dangerous context in strict mode
                is_medium = (f.severity.lower() == 'medium')
                if (is_doc and not in_danger) or (is_medium and not in_danger):
                    continue
                # Suppress extremely long code-line findings (likely data)
                if isinstance(f.line_content, str) and len(f.line_content) > 200 and not in_danger:
                    continue
            filtered_findings.append(f)
        
        # Convert findings to dictionaries and include small code snippet context
        return [self._finding_to_dict(finding, content) for finding in filtered_findings]
    
    def _apply_generic_rules(self, content: str, lines: List[str], file_path: Path, language: Optional[str]) -> List[Finding]:
        """Apply language-agnostic rules."""
        findings = []

        # Restrict generic rules to code-like languages to reduce false positives
        code_langs = {
            'python','javascript','typescript','java','go','ruby','php','c','cpp','csharp','rust',
            'swift','kotlin','scala','dart','r','shell','powershell','batch'
        }
        if language not in code_langs:
            return findings
        
        # Rule 1: Direct prompt injection - user input concatenated into prompts
        findings.extend(self._find_direct_prompt_injection(content, lines, file_path))
        
        # Rule 2: System prompt pollution - user content in system messages
        findings.extend(self._find_system_prompt_pollution(content, lines, file_path))
        
        # Rule 3: Template injection patterns
        findings.extend(self._find_template_injection(content, lines, file_path))
        
        # Rule 4: Unsafe string formatting
        findings.extend(self._find_unsafe_formatting(content, lines, file_path))
        
        # Rule 5: Hardcoded prompts with user placeholders
        findings.extend(self._find_hardcoded_prompts(content, lines, file_path))
        
        return findings
    
    def _apply_language_specific_rules(self, content: str, lines: List[str], file_path: Path, language: str) -> List[Finding]:
        """Apply language-specific rules."""
        findings = []
        
        if language == 'python':
            findings.extend(self._apply_python_rules(content, lines, file_path))
        elif language == 'javascript':
            findings.extend(self._apply_javascript_rules(content, lines, file_path))
        elif language == 'typescript':
            findings.extend(self._apply_typescript_rules(content, lines, file_path))
        
        return findings
    
    def _find_direct_prompt_injection(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Find direct prompt injection patterns."""
        findings = []
        
        # Patterns for user input being concatenated into prompts
        patterns = [
            # User input + prompt
            (r'(\w+)\s*\+\s*["\']([^"\']*prompt[^"\']*)["\']', 'User input concatenated with prompt'),
            (r'["\']([^"\']*prompt[^"\']*)["\']\s*\+\s*(\w+)', 'Prompt concatenated with user input'),
            
            # Variable assignment patterns
            (r'(\w+)\s*=\s*(\w+)\s*\+\s*["\']([^"\']*prompt[^"\']*)["\']', 'Variable assignment with prompt injection'),
            (r'(\w+)\s*=\s*["\']([^"\']*prompt[^"\']*)["\']\s*\+\s*(\w+)', 'Variable assignment with prompt injection'),
            
            # Function calls with concatenation
            (r'(\w+)\([^)]*\+\s*["\']([^"\']*prompt[^"\']*)["\']', 'Function call with prompt injection'),
            (r'(\w+)\(["\']([^"\']*prompt[^"\']*)["\']\s*\+\s*[^)]*\)', 'Function call with prompt injection'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-001',
                    severity='high',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path
                ))
        
        return findings
    
    def _find_system_prompt_pollution(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Find system prompt pollution patterns."""
        findings = []
        
        # Patterns for user content in system messages
        patterns = [
            # System role with user content
            (r'role\s*[:=]\s*["\']system["\']\s*[,}]', 'System message role field'),
            (r'content\s*[:=]\s*["\'][^"\']*\{[^}]*\}[^"\']*["\']', 'Message content includes placeholder'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-002',
                    severity='critical',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path
                ))
        
        return findings
    
    def _find_template_injection(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Find template injection patterns."""
        findings = []
        
        # Template injection patterns (narrowed to prompt/content contexts)
        patterns = [
            # Prompt variable assigned from formatted string
            (r'\b(prompt|system_prompt|user_prompt)\s*=\s*(["\"])((?:(?!\2).)*\{[^}]*\}(?:(?!\2).)*)\2', 'Prompt variable with placeholder'),
            (r'\b(prompt|system_prompt|user_prompt)\s*=\s*f["\"]((?:(?!\").)*\{[^}]*\}(?:(?!\").)*)["\"]', 'Prompt variable f-string with user variable'),
            (r'\b(prompt|system_prompt|user_prompt)\s*=\s*["\"][^"\']*["\"]\s*\.\s*format\s*\([^)]*\)', 'Prompt variable using .format'),
            
            # Object content field built with placeholders
            (r'content\s*[:=]\s*f["\"][^"\']*\{[^}]*\}[^"\']*["\"]', 'Content f-string with user variable'),
            (r'content\s*[:=]\s*["\"][^"\']*\{[^}]*\}[^"\']*["\"]', 'Content string with placeholder'),
            (r'content\s*[:=]\s*["\"][^"\']*["\"]\s*\.\s*format\s*\([^)]*\)', 'Content string using .format'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-003',
                    severity='high',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path
                ))
        
        return findings
    
    def _find_unsafe_formatting(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Find unsafe string formatting patterns."""
        findings = []
        
        # Unsafe formatting patterns
        patterns = [
            # % formatting with user input
            (r'["\']([^"\']*%[^"\']*)["\']\s*%\s*(\w+)', 'String formatting with user variable'),
            
            # eval with user input
            (r'eval\([^)]*\)', 'Eval with user input'),
            (r'exec\([^)]*\)', 'Exec with user input'),
            
            # Dynamic imports
            (r'__import__\([^)]*\)', 'Dynamic import with user input'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-004',
                    severity='critical',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path
                ))
        
        return findings
    
    def _find_hardcoded_prompts(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Find hardcoded prompts with user placeholders."""
        findings = []
        
        # Hardcoded prompt patterns limited to LLM-related contexts
        patterns = [
            # Prompt variables
            (r'\b(prompt|system_prompt|user_prompt)\s*=\s*["\"][^"\']*(\{user|\{input|\{query)[^"\']*["\"]', 'Hardcoded prompt with user placeholder'),
            (r'\b(prompt|system_prompt|user_prompt)\s*=\s*f["\"][^"\']*\{[^}]*\}[^"\']*["\"]', 'Hardcoded prompt f-string with variable'),
            # OpenAI/LLM messages content fields with placeholders
            (r'messages\s*[:=]\s*\[[^\]]*content\s*[:=]\s*["\"][^"\']*\{[^}]*\}[^"\']*["\"][^\]]*\]', 'Messages content with placeholder'),
            (r'content\s*[:=]\s*["\"][^"\']*(\{user|\{input|\{query)[^"\']*["\"]', 'Content with user placeholder'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-005',
                    severity='medium',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path
                ))
        
        return findings
    
    def _apply_python_rules(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Apply Python-specific rules."""
        findings = []
        
        # Python-specific patterns
        patterns = [
            # OpenAI API patterns
            (r'openai\.ChatCompletion\.create\([^)]*messages\s*=\s*\[[^\]]*\{[^}]*content[^}]*\{[^}]*\}[^}]*\}[^\]]*\]', 'OpenAI API with user input in messages'),
            (r'openai\.Completion\.create\([^)]*prompt\s*=\s*[^)]*\+[^)]*\)', 'OpenAI Completion with concatenated prompt'),
            
            # LangChain patterns
            (r'PromptTemplate\([^)]*input_variables\s*=\s*\[[^\]]*\]', 'LangChain PromptTemplate with user variables'),
            (r'LLMChain\([^)]*prompt\s*=\s*[^)]*\)', 'LangChain with user input'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-PY-001',
                    severity='high',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path,
                    language='python'
                ))
        
        return findings
    
    def _apply_javascript_rules(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Apply JavaScript-specific rules."""
        findings = []
        
        # JavaScript-specific patterns
        patterns = [
            # OpenAI API patterns
            (r'openai\.chat\.completions\.create\([^)]*messages\s*:\s*\[[^\]]*\{[^}]*content[^}]*\{[^}]*\}[^}]*\}[^\]]*\]', 'OpenAI API with user input in messages'),
            (r'openai\.completions\.create\([^)]*prompt\s*:\s*[^)]*\+[^)]*\)', 'OpenAI Completion with concatenated prompt'),
            
            # Template literals with user input ONLY in prompt/content contexts
            (r'\b(prompt|content|systemPrompt|userPrompt)\s*=\s*`([^`]*\$\{[^}]*\}[^`]*)`', 'Template literal prompt/content assignment with user variable'),
            (r'content\s*:\s*`([^`]*\$\{[^}]*\}[^`]*)`', 'Object content with template literal user variable'),
        ]
        
        for pattern, message in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = self._get_line_number(content, match.start())
                findings.append(Finding(
                    rule_id='PI-JS-001',
                    severity='high',
                    message=message,
                    line_number=line_num,
                    line_content=lines[line_num - 1] if line_num <= len(lines) else '',
                    context=match.group(0),
                    file_path=file_path,
                    language='javascript'
                ))
        
        return findings
    
    def _apply_typescript_rules(self, content: str, lines: List[str], file_path: Path) -> List[Finding]:
        """Apply TypeScript-specific rules."""
        # TypeScript rules are similar to JavaScript for now
        return self._apply_javascript_rules(content, lines, file_path)
    
    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a character position in content."""
        return content[:position].count('\n') + 1
    
    def _finding_to_dict(self, finding: Finding, content: Optional[str] = None) -> Dict[str, Any]:
        """Convert Finding object to dictionary."""
        # Build small code snippet of +/- 2 lines around the finding
        snippet = None
        reasons_list = None
        if content:
            try:
                lines = content.split('\n')
                start_idx = max(0, finding.line_number - 3)
                end_idx = min(len(lines), finding.line_number + 2)
                snippet_lines = lines[start_idx:end_idx]
                snippet = '\n'.join(snippet_lines)
            except Exception:
                snippet = None
        # Extract reasons list from message's appended context, if present
        try:
            msg = finding.message or ''
            if '(Context:' in msg:
                ctx = msg.split('(Context:', 1)[1].rstrip(')')
                ctx = ctx.replace('Context:', '').strip()
                raw = [s.strip() for s in ctx.split(',') if s.strip()]
                if raw:
                    reasons_list = raw[:2]
        except Exception:
            reasons_list = None

        return {
            'rule_id': finding.rule_id,
            'severity': finding.severity,
            'message': finding.message,
            'line_number': finding.line_number,
            'line': finding.line_number,
            'line_no': finding.line_number,
            'line_content': finding.line_content,
            'code_snippet': snippet,
            'reasons': reasons_list,
            'context': finding.context,
            'file_path': str(finding.file_path),
            'language': finding.language,
            'confidence': finding.confidence
        }
    
    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default detection rules."""
        return {
            'PI-001': {
                'name': 'Direct Prompt Injection',
                'description': 'User input directly concatenated into AI prompts',
                'severity': 'high'
            },
            'PI-002': {
                'name': 'System Prompt Pollution',
                'description': 'User content mixed with system instructions',
                'severity': 'critical'
            },
            'PI-003': {
                'name': 'Template Injection',
                'description': 'Unsafe template usage with user input',
                'severity': 'high'
            },
            'PI-004': {
                'name': 'Unsafe Formatting',
                'description': 'Unsafe string formatting with user input',
                'severity': 'critical'
            },
            'PI-005': {
                'name': 'Hardcoded Prompts',
                'description': 'Hardcoded prompts with user placeholders',
                'severity': 'medium'
            }
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        # This would compile all patterns used in the rules
        pass
