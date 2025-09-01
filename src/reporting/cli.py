"""
CLI report generator for scan results.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.progress import Progress
from rich import box
from rich.markup import escape


class CLIReportGenerator:
    """Generates CLI-formatted reports for scan results."""
    
    def __init__(self):
        self.console = Console()
    
    def generate_report(
        self,
        scan_data: Dict[str, Any],
        severity_filter: Optional[List[str]] = None,
        summary_only: bool = False,
        hide_code: bool = False,
        hide_context: bool = False,
    ):
        """
        Generate and display a CLI report.
        
        Args:
            scan_data: Scan results data
            severity_filter: Optional list of severity levels to include
        """
        results = scan_data.get('results', [])
        summary = scan_data.get('summary')
        
        # Filter results by severity if specified
        if severity_filter:
            results = self._filter_by_severity(results, severity_filter)
        
        # Display summary
        self._display_summary(summary, scan_data.get('scan_path', ''))
        
        # Display findings
        if not summary_only and results:
            self._display_findings(results, hide_code=hide_code, hide_context=hide_context)
        else:
            self.console.print(Panel(
                "[green]No vulnerabilities found![/green]\n"
                "Your codebase appears to be secure against prompt injection attacks.",
                title="Scan Complete",
                border_style="green"
            ))
    
    def _display_summary(self, summary: Any, scan_path: str):
        """Display scan summary."""
        if not summary:
            return
        
        # Create summary table
        table = Table(title="Scan Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Scan Path", scan_path)
        table.add_row("Total Files", str(summary.total_files))
        table.add_row("Scanned Files", str(summary.scanned_files))
        table.add_row("Skipped Files", str(summary.skipped_files))
        table.add_row("Total Findings", str(summary.total_findings))
        table.add_row("Scan Duration", f"{summary.scan_duration:.2f}s")
        
        self.console.print(table)
        
        # Display findings by severity
        if summary.findings_by_severity:
            self._display_severity_breakdown(summary.findings_by_severity)
        
        # Display findings by language
        if summary.findings_by_language:
            self._display_language_breakdown(summary.findings_by_language)
        
        self.console.print()  # Add spacing
    
    def _display_severity_breakdown(self, severity_counts: Dict[str, int]):
        """Display findings breakdown by severity."""
        table = Table(title="Findings by Severity", box=box.ROUNDED)
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")
        
        severity_colors = {
            'critical': 'red',
            'high': 'bright_red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'cyan'
        }
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity in severity_counts:
                color = severity_colors.get(severity, 'white')
                if color == 'red':
                    styled_severity = f"[red]{severity.title()}[/red]"
                elif color == 'bright_red':
                    styled_severity = f"[bright_red]{severity.title()}[/bright_red]"
                elif color == 'yellow':
                    styled_severity = f"[yellow]{severity.title()}[/yellow]"
                elif color == 'blue':
                    styled_severity = f"[blue]{severity.title()}[/blue]"
                elif color == 'cyan':
                    styled_severity = f"[cyan]{severity.title()}[/cyan]"
                else:
                    styled_severity = f"[white]{severity.title()}[/white]"
                table.add_row(
                    styled_severity,
                    str(severity_counts[severity])
                )
        
        self.console.print(table)
    
    def _display_language_breakdown(self, language_counts: Dict[str, int]):
        """Display findings breakdown by language."""
        table = Table(title="Findings by Language", box=box.ROUNDED)
        table.add_column("Language", style="bold")
        table.add_column("Count", justify="right")
        
        for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            table.add_row(language.title(), str(count))
        
        self.console.print(table)
    
    def _display_findings(self, results: List[Any], hide_code: bool = False, hide_context: bool = False):
        """Display all findings."""
        # Group findings by file
        files_with_findings = [r for r in results if r.findings]
        
        if not files_with_findings:
            return
        
        self.console.print(Panel(
            f"Found [red]{sum(len(r.findings) for r in files_with_findings)}[/red] vulnerabilities across [blue]{len(files_with_findings)}[/blue] files",
            title="Vulnerabilities Found",
            border_style="red"
        ))
        
        # Display findings by file
        for result in files_with_findings:
            self._display_file_findings(result, hide_code=hide_code, hide_context=hide_context)
    
    def _display_file_findings(self, result: Any, hide_code: bool = False, hide_context: bool = False):
        """Display findings for a single file."""
        file_path = result.file_path
        findings = result.findings
        
        if not findings:
            return
        
        # File header
        self.console.print(f"\n[bold blue]📁 {escape(str(file_path))}[/bold blue]")
        if result.language:
            self.console.print(f"[dim]Language: {result.language}[/dim]")
        
        # Group findings by severity
        findings_by_severity = {}
        for finding in findings:
            severity = finding.get('severity', 'unknown')
            if severity not in findings_by_severity:
                findings_by_severity[severity] = []
            findings_by_severity[severity].append(finding)
        
        # Display findings by severity
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if severity in findings_by_severity:
                self._display_severity_findings(severity, findings_by_severity[severity], hide_code=hide_code, hide_context=hide_context)
    
    def _display_severity_findings(self, severity: str, findings: List[Dict[str, Any]], hide_code: bool = False, hide_context: bool = False):
        """Display findings for a specific severity level."""
        severity_colors = {
            'critical': 'red',
            'high': 'bright_red',
            'medium': 'yellow',
            'low': 'blue',
            'info': 'cyan'
        }
        
        color = severity_colors.get(severity, 'white')
        
        for finding in findings:
            # Create finding panel
            rule_id = finding.get('rule_id', 'Unknown')
            message = escape(finding.get('message', 'No description'))
            line_number = finding.get('line_number', 0)
            line_content = escape(finding.get('line_content', '').strip())
            context = escape(finding.get('context', ''))
            
            # Format the finding
            confidence = finding.get('confidence', 1.0)
            confidence_text = f"Confidence: {confidence:.1f}"
            
            content = f"[bold]{message}[/bold]\n"
            content += f"Rule: [dim]{rule_id}[/dim]\n"
            content += f"Line: [yellow]{line_number}[/yellow]\n"
            content += f"{confidence_text}\n"
            
            if line_content and not hide_code:
                content += f"Code: [white]{line_content}[/white]\n"
            
            if context and not hide_context:
                content += f"Context: [dim]{context}[/dim]"
            
            # Create panel
            if color == 'red':
                title = f"[red]{severity.title()}[/red]"
            elif color == 'bright_red':
                title = f"[bright_red]{severity.title()}[/bright_red]"
            elif color == 'yellow':
                title = f"[yellow]{severity.title()}[/yellow]"
            elif color == 'blue':
                title = f"[blue]{severity.title()}[/blue]"
            elif color == 'cyan':
                title = f"[cyan]{severity.title()}[/cyan]"
            else:
                title = f"[white]{severity.title()}[/white]"
            
            panel = Panel(
                content,
                title=title,
                border_style=color,
                padding=(0, 1)
            )
            
            self.console.print(panel)
    
    def _filter_by_severity(self, results: List[Any], severity_filter: List[str]) -> List[Any]:
        """Filter results by severity level."""
        filtered_results = []
        
        for result in results:
            filtered_findings = [
                finding for finding in result.findings
                if finding.get('severity', 'unknown') in severity_filter
            ]
            
            if filtered_findings:
                # Create a new result with filtered findings
                filtered_result = type(result)(
                    file_path=result.file_path,
                    findings=filtered_findings,
                    scan_time=result.scan_time,
                    file_size=result.file_size,
                    language=result.language
                )
                filtered_results.append(filtered_result)
        
        return filtered_results
    
    def display_recommendations(self):
        """Display general security recommendations."""
        recommendations = [
            "🔒 Always validate and sanitize user input before using it in prompts",
            "🛡️ Use parameterized prompts instead of string concatenation",
            "📝 Separate system instructions from user content",
            "🔍 Implement input validation and output encoding",
            "📚 Follow the principle of least privilege for AI model access",
            "🔄 Regularly audit and update prompt injection detection rules",
            "🧪 Test your prompts with adversarial inputs",
            "📋 Document your prompt security practices"
        ]
        
        self.console.print(Panel(
            "\n".join(recommendations),
            title="Security Recommendations",
            border_style="green"
        ))
