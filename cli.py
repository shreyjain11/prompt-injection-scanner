#!/usr/bin/env python3
"""
Prompt Injection Scanner CLI
A tool to detect potential prompt injection vulnerabilities in codebases.
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
import json
import yaml

from src.scanner.core import PromptScanner
from src.reporting.cli import CLIReportGenerator
from src.utils.file_utils import validate_path
from src.utils.repo_fetch import parse_github_url, fetch_github_repo_to_dir
from src.rules.loader import RuleLoader
from src.scanner.indexer import RepositoryIndexer

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Prompt Injection Scanner - Detect AI security vulnerabilities in codebases."""
    pass

@cli.command()
@click.argument('path_or_url')
@click.option('--output', '-o', type=click.Choice(['cli', 'json', 'html']), default='cli', 
              help='Output format for the report')
@click.option('--severity', '-s', multiple=True,
              type=click.Choice(['critical', 'high', 'medium', 'low', 'info']),
              help='Filter by severity (repeatable, e.g., -s high -s critical)')
@click.option('--exclude', '-e', multiple=True, 
              help='Patterns to exclude (e.g., node_modules, dist)')
@click.option('--parallel', '-p', type=int, default=4, 
              help='Number of parallel workers')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--no-cache', is_flag=True, help='Disable caching')
@click.option('--no-progress', is_flag=True, help='Disable progress spinner/bars')
@click.option('--min-confidence', type=float, default=0.0, help='Only show findings with confidence >= N (0.0-1.0)')
@click.option('--summary-only', is_flag=True, help='Only print the summary and counts')
@click.option('--hide-code', is_flag=True, help='Hide code line snippets in findings')
@click.option('--hide-context', is_flag=True, help='Hide context snippets in findings')
@click.option('--strict', is_flag=True, help='High-precision mode: suppress borderline cases')
def scan(path_or_url, output, severity, exclude, parallel, verbose, no_cache, no_progress, min_confidence, summary_only, hide_code, hide_context, strict):
    """Scan a codebase for prompt injection vulnerabilities."""
    
    # Support GitHub URLs directly
    repo_temp_dir = None
    input_str = str(path_or_url)
    if input_str.startswith('http://') or input_str.startswith('https://'):
        if parse_github_url(input_str) is None:
            console.print("[bold red]Only public GitHub URLs are supported for URL scans.[/bold red]")
            sys.exit(1)
        if verbose:
            console.print(f"[bold blue]Fetching repository:[/bold blue] {input_str}")
        repo_temp_dir = fetch_github_repo_to_dir(input_str)
        path = repo_temp_dir
    else:
        path = Path(input_str).resolve()
        if not validate_path(path):
            console.print(f"[bold red]Invalid path:[/bold red] {path}")
            sys.exit(1)
    
    if verbose:
        console.print(f"[bold blue]Scanning:[/bold blue] {path}")
        console.print(f"[bold blue]Output format:[/bold blue] {output}")
        console.print(f"[bold blue]Severity filter:[/bold blue] {severity or 'All'}")
        console.print(f"[bold blue]Exclude patterns:[/bold blue] {exclude or 'None'}")
        console.print(f"[bold blue]Parallel workers:[/bold blue] {parallel}")
    
    try:
        # Initialize scanner
        scanner = PromptScanner(
            exclude_patterns=list(exclude),
            parallel_workers=parallel,
            use_cache=not no_cache,
            verbose=verbose
        )
        # Wire engine thresholds/mode
        scanner.rule_engine.min_confidence_threshold = float(min_confidence)
        scanner.rule_engine.strict = bool(strict)
        
        # Scan the repository
        results = None
        if no_progress:
            results = scanner.scan(path)
        else:
            progress_console = console if output == 'cli' else Console(file=sys.stderr)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=progress_console
            ) as progress:
                task = progress.add_task("Scanning repository...", total=None)
                results = scanner.scan(path)
                progress.update(task, description="Generating report...")
        
        # Generate report
        if min_confidence > 0:
            # Filter results by min confidence
            filtered = []
            for r in results['results']:
                kept = [f for f in r.findings if f.get('confidence', 0) >= min_confidence]
                if kept:
                    new_r = type(r)(
                        file_path=r.file_path,
                        findings=kept,
                        scan_time=r.scan_time,
                        file_size=r.file_size,
                        language=r.language
                    )
                    filtered.append(new_r)
            results['results'] = filtered

        if output == 'cli':
            reporter = CLIReportGenerator()
            reporter.generate_report(
                results,
                severity_filter=severity,
                summary_only=summary_only,
                hide_code=hide_code,
                hide_context=hide_context,
            )
        elif output == 'json':
            console.print(_serialize_scan_results_to_json(results))
        elif output == 'html':
            # TODO: Implement HTML reporter
            console.print("[yellow]HTML output not yet implemented[/yellow]")
            
    except Exception as e:
        # Escape brackets to avoid Rich markup errors
        safe_msg = str(e).replace('[', '\\[').replace(']', '\\]')
        console.print(f"[bold red]Error:[/bold red] {safe_msg}")
        if verbose:
            console.print_exception()
        sys.exit(1)
    finally:
        # Best-effort cleanup for temp repo
        if repo_temp_dir:
            try:
                import shutil
                shutil.rmtree(repo_temp_dir, ignore_errors=True)
            except Exception:
                pass

@cli.command()
@click.option('--examples-only', is_flag=True, help='Run benchmark against rule examples only')
def rules():
    """List available detection rules."""
    loader = RuleLoader()
    stats = loader.get_rule_statistics()
    console.print(Panel.fit(
        f"Loaded rules for {stats['total_languages']} languages\n"
        f"Total rules: {stats['total_rules']}\n"
        f"By severity: {stats['rules_by_severity']}",
        title="Rules",
        border_style="blue"
    ))
    # List languages and category counts
    for language, lang_stats in stats['languages'].items():
        console.print(f"- [bold]{language}[/bold]: {lang_stats['total_rules']} rules in {lang_stats['categories']} categories")

@cli.command()
@click.option('--language', '-l', multiple=True, help='Limit to specific language(s)')
@click.option('--manifest', type=click.Path(exists=False, dir_okay=False), help='Path to benchmark manifest (YAML)')
@click.option('--min-confidence', type=float, default=0.0, help='Minimum confidence threshold for findings (0.0-1.0)')
@click.option('--strict', is_flag=True, help='High-precision mode: suppress borderline cases')
@click.option('--tune', is_flag=True, help='Auto-tune threshold/strict to optimize F1 (bench-only)')
@click.option('--min-precision', type=float, default=0.0, help='Precision constraint during tuning (0.0-1.0)')
@click.option('--min-recall', type=float, default=0.0, help='Recall constraint during tuning (0.0-1.0)')
def bench(language, manifest, min_confidence, strict, tune, min_precision, min_recall):
    """Run a quick benchmark using YAML rule examples as ground truth."""
    # If no manifest is provided, use packaged manifest
    if manifest:
        manifest_path = Path(manifest)
        with open(manifest_path, 'r') as f:
            bench = yaml.safe_load(f)
    else:
        # Try packaged manifest
        default_manifest = Path(__file__).parent / 'src' / 'benchmarks' / 'manifest.yaml'
        if not default_manifest.exists():
            # Fallback to installed package path
            try:
                from importlib import resources
                import src.benchmarks
                with resources.files(src.benchmarks).joinpath('manifest.yaml').open('r') as f:
                    bench = yaml.safe_load(f)
            except Exception:
                console.print("[yellow]No benchmark manifest found[/yellow]")
                bench = None
        else:
            with open(default_manifest, 'r') as f:
                bench = yaml.safe_load(f)

    loader = RuleLoader()
    selected_langs = set(language) if language else set(loader.get_supported_languages())

    # language to extension for realistic file suffix
    lang_ext = {
        'python': '.py',
        'javascript': '.js',
        'typescript': '.ts',
    }

    def run_eval(threshold: float, use_strict: bool):
        total = tp = fp = fn = 0
        from src.scanner.rule_engine import RuleEngine
        engine = RuleEngine()
        engine.min_confidence_threshold = float(threshold)
        engine.strict = bool(use_strict)

        # 1) Evaluate built-in rule examples
        for lang in selected_langs:
            rule_set = loader.get_rule_set(lang)
            if not rule_set:
                continue
            for category, rules in rule_set.rules.items():
                for rule in rules:
                    for ex in rule.examples.get('vulnerable', []):
                        total += 1
                        path = Path(f"bench_{lang}{lang_ext.get(lang, '.txt')}")
                        findings = engine.apply_rules(ex, path, language=lang)
                        tp += 1 if findings else 0
                        fn += 0 if findings else 1
                    for ex in rule.examples.get('secure', []):
                        total += 1
                        path = Path(f"bench_{lang}{lang_ext.get(lang, '.txt')}")
                        findings = engine.apply_rules(ex, path, language=lang)
                        fp += 1 if findings else 0

        # 2) Evaluate manifest suites if present
        if bench and 'suites' in bench:
            for suite_name, suite in bench['suites'].items():
                for case in suite.get('cases', []):
                    lang = case.get('language')
                    if selected_langs and lang not in selected_langs:
                        continue
                    label = case.get('label', 'vulnerable')
                    code = case.get('code', '')
                    total += 1
                    path = Path(f"bench_{lang}{lang_ext.get(lang, '.txt')}")
                    findings = engine.apply_rules(code, path, language=lang)
                    if label == 'vulnerable':
                        tp += 1 if findings else 0
                        fn += 0 if findings else 1
                    else:
                        fp += 1 if findings else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        return {
            'total': total,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'threshold': threshold,
            'strict': use_strict,
        }

    if tune:
        candidates = []
        # Sweep thresholds and strict flag
        for thr in [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            for s in [False, True]:
                res = run_eval(thr, s)
                if res['precision'] >= min_precision and res['recall'] >= min_recall:
                    candidates.append(res)
        if not candidates:
            console.print(Panel.fit("No configuration met the constraints", title="Benchmark", border_style="red"))
            return
        # Pick best by F1, tie-break by higher precision then higher recall
        best = sorted(candidates, key=lambda r: (r['f1'], r['precision'], r['recall']), reverse=True)[0]
        console.print(Panel.fit(
            f"Tuned best config\n"
            f"Threshold: {best['threshold']:.2f}\nStrict: {best['strict']}\n"
            f"TP: {best['tp']}  FP: {best['fp']}  FN: {best['fn']}\n"
            f"Precision: {best['precision']:.2f}  Recall: {best['recall']:.2f}  F1: {best['f1']:.2f}",
            title="Benchmark (Tuned)", border_style="green"
        ))
        return

    # Non-tuned single run
    res = run_eval(min_confidence, strict)
    precision = res['precision']
    recall = res['recall']
    console.print(Panel.fit(
        f"Examples evaluated: {res['total']}\nTP: {res['tp']}  FP: {res['fp']}  FN: {res['fn']}\nPrecision: {precision:.2f}  Recall: {recall:.2f}",
        title="Benchmark",
        border_style="green"
    ))

@cli.command()
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--exclude', '-e', multiple=True, help='Patterns to exclude (e.g., node_modules, dist)')
@click.option('--include', '-i', multiple=True, help='Patterns to explicitly include')
@click.option('--max-bytes', type=int, default=None, help='Maximum file size to index in bytes')
@click.option('--output', '-o', type=click.Path(dir_okay=False), default=None, help='Write JSON index to file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def index(path, exclude, include, max_bytes, output, verbose):
    """Index repository files and output a JSON index."""
    root = Path(path).resolve()
    if verbose:
        console.print(f"[bold blue]Indexing:[/bold blue] {root}")
        console.print(f"[bold blue]Exclude patterns:[/bold blue] {list(exclude) or 'None'}")
        console.print(f"[bold blue]Include patterns:[/bold blue] {list(include) or 'None'}")
        console.print(f"[bold blue]Max bytes:[/bold blue] {max_bytes or 'None'}")

    try:
        indexer = RepositoryIndexer(
            exclude_patterns=list(exclude),
            include_patterns=list(include),
            max_file_size_bytes=max_bytes,
            verbose=verbose,
        )
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Indexing repository...", total=None)
            data = indexer.index(root)
            progress.update(task, description="Preparing output...")

        output_json = json.dumps(data, indent=2)
        if output:
            Path(output).write_text(output_json)
            console.print(Panel.fit(
                f"Indexed {data['total_files']} files\nSaved to: {output}",
                title="Index Complete",
                border_style="green"
            ))
        else:
            console.print(output_json)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)

@cli.command()
def version():
    """Show version information."""
    console.print(Panel.fit(
        "[bold blue]Prompt Injection Scanner[/bold blue]\n"
        "[green]Version:[/green] 0.1.0\n"
        "[green]Author:[/green] Shrey Jain\n"
        "[green]Description:[/green] Detect prompt injection vulnerabilities in codebases",
        title="About"
    ))

if __name__ == '__main__':
    # Allow `python cli.py <path_or_url>` without subcommand for local dev
    args = sys.argv[1:]
    known = {"scan", "rules", "version", "index", "bench", "--help", "-h", "--version"}
    if args and not args[0].startswith('-') and args[0] not in known:
        sys.argv.insert(1, 'scan')
    cli()

# Console entrypoint that allows `prompt-scan <path_or_url>`
def entry():
    args = sys.argv[1:]
    known = {"scan", "rules", "version", "index", "bench", "--help", "-h", "--version"}
    if args and not args[0].startswith('-') and args[0] not in known:
        sys.argv.insert(1, 'scan')
    cli()

# ---------- Helpers ----------
def _serialize_scan_results_to_json(scan_data):
    """Serialize scan results dict to pretty JSON string."""
    summary = scan_data.get('summary')
    summary_dict = None
    if summary is not None:
        summary_dict = {
            'total_files': summary.total_files,
            'scanned_files': summary.scanned_files,
            'skipped_files': summary.skipped_files,
            'total_findings': summary.total_findings,
            'scan_duration': summary.scan_duration,
            'findings_by_severity': summary.findings_by_severity,
            'findings_by_language': summary.findings_by_language,
        }

    results = []
    for r in scan_data.get('results', []):
        results.append({
            'file_path': str(r.file_path),
            'findings': r.findings,
            'scan_time': r.scan_time,
            'file_size': r.file_size,
            'language': r.language,
        })

    payload = {
        'scan_path': scan_data.get('scan_path'),
        'scan_timestamp': scan_data.get('scan_timestamp'),
        'summary': summary_dict,
        'results': results,
    }
    return json.dumps(payload, indent=2)




