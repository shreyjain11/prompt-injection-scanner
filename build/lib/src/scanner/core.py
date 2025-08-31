"""
Core scanning engine for prompt injection detection.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .file_processor import FileProcessor
from .rule_engine import RuleEngine
from .cache import ScanCache
from ..utils.file_utils import get_scannable_files
from ..config.manager import ConfigManager


@dataclass
class ScanResult:
    """Result of a single file scan."""
    file_path: Path
    findings: List[Dict[str, Any]]
    scan_time: float
    file_size: int
    language: Optional[str] = None


@dataclass
class ScanSummary:
    """Summary of the entire scan."""
    total_files: int
    scanned_files: int
    skipped_files: int
    total_findings: int
    scan_duration: float
    findings_by_severity: Dict[str, int]
    findings_by_language: Dict[str, int]


class PromptScanner:
    """Main scanner class that orchestrates the scanning process."""
    
    def __init__(
        self,
        exclude_patterns: Optional[List[str]] = None,
        parallel_workers: int = 4,
        use_cache: bool = True,
        verbose: bool = False,
        config: Optional[ConfigManager] = None
    ):
        # Initialize configuration
        self.config = config or ConfigManager()
        
        # Override config with explicit parameters
        self.exclude_patterns = exclude_patterns or self.config.get_exclude_patterns()
        self.parallel_workers = parallel_workers or self.config.get_parallel_workers()
        self.use_cache = use_cache if use_cache is not None else self.config.should_use_cache()
        self.verbose = verbose or self.config.is_verbose()
        
        # Initialize components
        self.file_processor = FileProcessor(
            max_file_size=self.config.get_max_file_size_mb() * 1024 * 1024
        )
        self.rule_engine = RuleEngine()
        self.cache = ScanCache(
            ttl=self.config.get_cache_ttl_hours() * 3600
        ) if self.use_cache else None
        
    def scan(self, path: Path) -> Dict[str, Any]:
        """
        Scan a directory for prompt injection vulnerabilities.
        
        Args:
            path: Path to the directory to scan
            
        Returns:
            Dictionary containing scan results and summary
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"Starting scan of: {path}")
        
        # Get all scannable files
        files = get_scannable_files(path, self.exclude_patterns)
        
        if self.verbose:
            print(f"Found {len(files)} files to scan")
        
        # Scan files (with caching if enabled)
        results = []
        skipped_files = 0
        
        if self.parallel_workers > 1:
            results, skipped_files = self._scan_parallel(files)
        else:
            results, skipped_files = self._scan_sequential(files)
        
        # Generate summary
        summary = self._generate_summary(results, time.time() - start_time, total_files=len(files), skipped_files=skipped_files)
        
        return {
            'results': results,
            'summary': summary,
            'scan_path': str(path),
            'scan_timestamp': time.time()
        }
    
    def _scan_parallel(self, files: List[Path]) -> tuple[List[ScanResult], int]:
        """Scan files using parallel workers.

        Returns tuple of (results, skipped_files_count)
        """
        results = []
        skipped = 0
        
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Submit all scan tasks
            future_to_file = {
                executor.submit(self._scan_single_file, file): file 
                for file in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    else:
                        skipped += 1
                except Exception as e:
                    if self.verbose:
                        print(f"Error scanning {file}: {e}")
                    skipped += 1
        
        return results, skipped
    
    def _scan_sequential(self, files: List[Path]) -> tuple[List[ScanResult], int]:
        """Scan files sequentially.

        Returns tuple of (results, skipped_files_count)
        """
        results = []
        skipped = 0
        
        for file in files:
            try:
                result = self._scan_single_file(file)
                if result:
                    results.append(result)
                else:
                    skipped += 1
            except Exception as e:
                if self.verbose:
                    print(f"Error scanning {file}: {e}")
                skipped += 1
        
        return results, skipped
    
    def _scan_single_file(self, file_path: Path) -> Optional[ScanResult]:
        """Scan a single file for vulnerabilities."""
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(file_path)
            if cached_result:
                return cached_result
        
        # Read and process file
        try:
            content = self.file_processor.read_file(file_path)
            if content is None:
                return None
            
            # Detect language
            language = self.file_processor.detect_language(file_path, content)
            
            # Apply rules
            start_time = time.time()
            findings = self.rule_engine.apply_rules(content, file_path, language)
            scan_time = time.time() - start_time
            
            # Create result
            result = ScanResult(
                file_path=file_path,
                findings=findings,
                scan_time=scan_time,
                file_size=len(content),
                language=language
            )
            
            # Cache result
            if self.cache:
                self.cache.set(file_path, result)
            
            return result
            
        except Exception as e:
            if self.verbose:
                print(f"Error processing {file_path}: {e}")
            return None
    
    def _generate_summary(self, results: List[ScanResult], total_duration: float, total_files: int, skipped_files: int) -> ScanSummary:
        """Generate a summary of the scan results."""
        total_findings = sum(len(r.findings) for r in results)
        
        # Count findings by severity
        findings_by_severity = {}
        findings_by_language = {}
        
        for result in results:
            for finding in result.findings:
                severity = finding.get('severity', 'unknown')
                findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
                
                if result.language:
                    findings_by_language[result.language] = findings_by_language.get(result.language, 0) + 1
        
        return ScanSummary(
            total_files=total_files,
            scanned_files=len(results),
            skipped_files=skipped_files,
            total_findings=total_findings,
            scan_duration=total_duration,
            findings_by_severity=findings_by_severity,
            findings_by_language=findings_by_language
        )
