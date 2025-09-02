
"""
Context analyzer for distinguishing between vulnerable and safe code patterns.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class ContextAnalyzer:
    """Analyzes code context to determine if patterns are actually vulnerable."""
    
    def __init__(self):
        # Safe contexts where user input is unlikely to be dangerous
        self.safe_contexts = {
            'python': [
                r'print\s*\([^)]*\)',  # print statements
                r'logging\.[a-z]+\s*\([^)]*\)',  # logging
                r'debug\s*\([^)]*\)',  # debug statements
                r'console\.log\s*\([^)]*\)',  # JavaScript console.log
                r'console\.error\s*\([^)]*\)',  # JavaScript console.error
                r'console\.warn\s*\([^)]*\)',  # JavaScript console.warn
                r'f"[^"]*\{[^}]*\}[^"]*"',  # f-strings in safe contexts
                r'"[^"]*\{[^}]*\}[^"]*"\.format\s*\([^)]*\)',  # .format() in safe contexts
                r'return\s+json\.dumps\([^)]*\)',  # returning JSON payloads
                r'logger\.(info|error|warning|debug)\s*\([^)]*\)',  # structured logging
            ],
            'javascript': [
                r'console\.log\s*\([^)]*\)',  # console.log
                r'console\.error\s*\([^)]*\)',  # console.error
                r'console\.warn\s*\([^)]*\)',  # console.warn
                r'`[^`]*\$\{[^}]*\}[^`]*`',  # template literals in safe contexts
            ]
        }
        
        # Dangerous contexts where user input is likely to be used in prompts
        self.dangerous_contexts = {
            'python': [
                r'openai\.ChatCompletion\.create\s*\([^)]*\)',
                r'openai\.Completion\.create\s*\([^)]*\)',
                r'langchain\.[a-zA-Z]+\s*\([^)]*\)',
                r'PromptTemplate\s*\([^)]*\)',
                r'LLMChain\s*\([^)]*\)',
                r'\bchat\s*\([^)]*\)',
                r'\bcompletion\s*\([^)]*\)',
                r'generate\s*\([^)]*\)',
                r'ask\s*\([^)]*\)',
                r'query\s*\([^)]*\)',
                r'\beval\s*\([^)]*\)',
                r'\bexec\s*\([^)]*\)'
            ],
            'javascript': [
                r'openai\.chat\.completions\.create\s*\([^)]*\)',
                r'openai\.completions\.create\s*\([^)]*\)',
                r'fetch\s*\([^)]*\)',  # API calls
                r'axios\.[a-z]+\s*\([^)]*\)',  # HTTP requests
                r'request\s*\([^)]*\)',  # HTTP requests
                r'`[^`]*\$\{[^}]*\}[^`]*`',  # template literal in code context
            ]
        }
        
        # Compile patterns for performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for performance."""
        self.compiled_safe = {}
        self.compiled_dangerous = {}
        
        for lang, patterns in self.safe_contexts.items():
            self.compiled_safe[lang] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
        for lang, patterns in self.dangerous_contexts.items():
            self.compiled_dangerous[lang] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def analyze_context(self, content: str, file_path: Path, language: Optional[str], 
                       line_number: int, context: str, base_severity: Optional[str] = None) -> Tuple[float, str]:
        """
        Compute a confidence score (0.0-1.0) that a finding is truly vulnerable.
        
        Args:
            content: Full file content
            file_path: Path to the file
            language: Detected language
            line_number: Line number of the finding
            context: The specific code context
            
        Returns:
            Tuple of (confidence_score in [0,1], reason)
        """
        if not language:
            return 0.6, "Unknown language, slight positive prior"
        
        # Get surrounding context (lines before and after)
        lines = content.split('\n')
        start_line = max(0, line_number - 3)
        end_line = min(len(lines), line_number + 3)
        surrounding_context = '\n'.join(lines[start_line:end_line])
        
        # Start with conservative prior and severity prior
        score = 0.35
        reasons: List[str] = []

        if base_severity:
            sev = base_severity.lower()
            sev_boost = {
                'critical': 0.25,
                'high': 0.15,
                'medium': 0.05,
                'low': 0.0,
                'info': -0.05,
            }.get(sev, 0.0)
            if sev_boost:
                score += sev_boost
                reasons.append(f"severity:{sev}")
        
        # Dangerous context increases confidence
        if self._is_in_dangerous_context(surrounding_context, language):
            score += 0.35
            reasons.append("dangerous context")
        
        # Safe context decreases confidence
        if self._is_in_safe_context(surrounding_context, language):
            score -= 0.4
            reasons.append("safe context")
        
        # Local patterns
        if self._is_dangerous_pattern(context, language):
            score += 0.2
            reasons.append("dangerous pattern")
        if self._is_safe_pattern(context, language):
            score -= 0.2
            reasons.append("safe pattern")
        
        # Heuristics by path or extension (markdown/text and data tend to be instructional)
        suffix = file_path.suffix.lower()
        if suffix in {'.md', '.markdown', '.txt'}:
            score -= 0.2
            reasons.append("documentation file")
        if suffix in {'.csv', '.tsv'}:
            score -= 0.3
            reasons.append("data file")
        if any(part in {"examples", "docs", "tests", "test", "samples"} for part in file_path.parts):
            score -= 0.3
            reasons.append("examples/docs/tests path")
        # Specific doc filenames like GUIDE or README variants
        name_lower = file_path.name.lower()
        if name_lower.endswith('guide.md') or name_lower.startswith('readme'):
            score -= 0.3
            reasons.append("guide/readme")
        
        # Variable analysis inside string templates
        var_names = self._extract_variables(context, language)
        if var_names:
            has_user_like = any(self.is_user_input_variable(v, context) for v in var_names)
            if has_user_like:
                score += 0.1
                reasons.append("user variable")
            else:
                score -= 0.25
                reasons.append("non-user variable")
        
        # LLM usage proximity heuristic: distance to LLM API usage
        llm_patterns = [
            r'openai\.', r'langchain', r'anthropic\.', r'gemini\.', r'groq\.', r'cohere\.',
            r'chat\.?completions?\.?create', r'Completion\.create', r'ChatCompletion\.create', r'messages\s*[:=]'
        ]
        distance = self._distance_to_any_pattern(lines, line_number, llm_patterns)
        if distance is not None:
            if distance <= 3:
                score += 0.25; reasons.append("llm proximity:<=3")
            elif distance <= 10:
                score += 0.15; reasons.append("llm proximity:<=10")
            elif distance <= 20:
                score += 0.1; reasons.append("llm proximity:<=20")
        assigns_prompt = re.search(r'\b(content|prompt)\s*[:=]', surrounding_context)
        if assigns_prompt and (distance is None or distance > 20):
            score -= 0.3
            reasons.append("assigns prompt without llm usage nearby")
        
        # Long-line penalty — data blobs are less likely to be code logic
        if isinstance(lines[line_number - 1] if 0 < line_number <= len(lines) else '', str):
            ln = lines[line_number - 1] if 0 < line_number <= len(lines) else ''
            if len(ln) > 400:
                score -= 0.35; reasons.append("very long line")
            elif len(ln) > 200:
                score -= 0.25; reasons.append("long line")

        # Clamp score
        score = max(0.0, min(1.0, score))
        reason = ", ".join(reasons) if reasons else "neutral"
        return score, reason

    def _distance_to_any_pattern(self, lines: List[str], line_number: int, patterns: List[str]) -> Optional[int]:
        """Return the distance in lines to the closest match of any pattern within ±50 lines.

        If none found, return None.
        """
        window_before = max(0, line_number - 50)
        window_after = min(len(lines), line_number + 50)
        compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
        nearest: Optional[int] = None
        for idx in range(window_before, window_after):
            text = lines[idx]
            if any(c.search(text) for c in compiled):
                dist = abs(idx + 1 - line_number)
                if nearest is None or dist < nearest:
                    nearest = dist
        return nearest
    
    def _is_in_dangerous_context(self, context: str, language: str) -> bool:
        """Check if the context is in a dangerous area."""
        if language not in self.compiled_dangerous:
            return False
        
        for pattern in self.compiled_dangerous[language]:
            if pattern.search(context):
                return True
        return False
    
    def _is_in_safe_context(self, context: str, language: str) -> bool:
        """Check if the context is in a safe area."""
        if language not in self.compiled_safe:
            return False
        
        for pattern in self.compiled_safe[language]:
            if pattern.search(context):
                return True
        return False
    
    def _is_safe_pattern(self, context: str, language: str) -> bool:
        """Check for specific safe patterns."""
        safe_patterns = {
            'python': [
                r'print\s*\([^)]*\)',  # print statements
                r'logging\.[a-z]+\s*\([^)]*\)',  # logging
                r'debug\s*\([^)]*\)',  # debug
                r'#.*',  # comments
                r'"""[\s\S]*"""',  # docstrings
                r"'''[\s\S]*'''",  # docstrings
                # CUDA device selection
                r"\.to\(f?'cuda:\\{[A-Za-z0-9_]+\\}'\)",
                r"device\s*=\s*f?'cuda:\\{[A-Za-z0-9_]+\\}'",
            ],
            'javascript': [
                r'console\.(log|error|warn)\s*\([^)]*\)',  # console
                r'//.*',  # comments
                r'/\*[\s\S]*\*/',  # block comments
                # UI-focused template literals
                r'className\s*=\s*`[\s\S]*`',
                r'style\s*=\s*\{\s*\{[\s\S]*`[\s\S]*`[\s\S]*\}\s*\}',
                r'addDebug(Log|Info)\s*\([^)]*`[\s\S]*`[^)]*\)',
                r'setMessage\s*\([^)]*`[\s\S]*`[^)]*\)',
                r'console\.[a-z]+\s*\([^)]*`[\s\S]*`[^)]*\)',
            ]
        }
        
        if language in safe_patterns:
            for pattern in safe_patterns[language]:
                if re.search(pattern, context, re.IGNORECASE):
                    return True
        return False
    
    def _is_dangerous_pattern(self, context: str, language: str) -> bool:
        """Check for specific dangerous patterns."""
        dangerous_patterns = {
            'python': [
                r'openai\.[a-zA-Z]+\.[a-zA-Z]+\s*\([^)]*\)',  # OpenAI API calls
                r'langchain\.[a-zA-Z]+\s*\([^)]*\)',  # LangChain calls
                r'prompt\s*[=+]\s*[^+]*\+',  # prompt concatenation
                r'messages\s*=\s*\[[^\]]*\{[^}]*content[^}]*\{[^}]*\}[^}]*\}[^\]]*\]',  # messages with user input
            ],
            'javascript': [
                r'openai\.[a-zA-Z]+\.[a-zA-Z]+\s*\([^)]*\)',  # OpenAI API calls
                r'messages\s*:\s*\[[^\]]*\{[^}]*content[^}]*\{[^}]*\}[^}]*\}[^\]]*\]',  # messages with user input
                r'prompt\s*[=+]\s*[^+]*\+',  # prompt concatenation
            ]
        }
        
        if language in dangerous_patterns:
            for pattern in dangerous_patterns[language]:
                if re.search(pattern, context, re.IGNORECASE):
                    return True
        return False
    
    def _extract_variables(self, context: str, language: Optional[str]) -> list[str]:
        """Extract variable names from template contexts for simple heuristics."""
        vars_found = []
        try:
            if language == 'python':
                vars_found += re.findall(r'\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}', context)
            if language == 'javascript':
                vars_found += re.findall(r'\$\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}', context)
        except Exception:
            pass
        return vars_found

    def is_user_input_variable(self, variable_name: str, context: str) -> bool:
        """Check if a variable is likely to contain user input."""
        user_input_indicators = [
            r'user_input',
            r'userInput',
            r'input',
            r'query',
            r'prompt',
            r'user_message',
            r'userMessage',
            r'request',
            r'data',
            r'content',
            r'text',
            r'string',
            r'value',
            r'param',
            r'arg',
            r'variable',
        ]
        
        for pattern in user_input_indicators:
            if re.search(pattern, variable_name, re.IGNORECASE):
                return True
        return False




