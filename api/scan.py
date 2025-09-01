from __future__ import annotations

import json
import shutil
from pathlib import Path
from flask import Flask, request, jsonify

# Local imports from the repo (works on Vercel and local)
from src.scanner.core import PromptScanner
from src.utils.repo_fetch import parse_github_url, fetch_github_repo_to_dir

try:
    from cli import _serialize_scan_results_to_json  # type: ignore
except Exception:
    _serialize_scan_results_to_json = None


app = Flask(__name__)


def _local_serialize(scan_data) -> str:
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


@app.route("/", methods=["POST", "GET"], strict_slashes=False)  # Works if Vercel strips the prefix
@app.route("/api/scan", methods=["POST", "GET"], strict_slashes=False)  # Works if Vercel keeps the full path
def scan_handler():
    if request.method == "GET":
        url = (request.args.get('url') or '').strip()
        min_confidence = float(request.args.get('min_confidence') or 0.0)
        strict = (request.args.get('strict') in ("1", "true", "True", "on"))
    else:
        data = request.get_json(silent=True) or {}
        url = (data.get('url') or '').strip()
        min_confidence = float(data.get('min_confidence', 0.0))
        strict = bool(data.get('strict', False))

    if not url or parse_github_url(url) is None:
        return jsonify({
            'error': 'Invalid or unsupported URL. Provide a public GitHub URL like https://github.com/owner/repo'
        }), 400

    repo_dir = None
    try:
        repo_dir = fetch_github_repo_to_dir(url)

        scanner = PromptScanner(
            exclude_patterns=[],
            parallel_workers=4,
            use_cache=False,
            verbose=False,
        )
        scanner.rule_engine.min_confidence_threshold = float(min_confidence)
        scanner.rule_engine.strict = bool(strict)

        scan_results = scanner.scan(Path(repo_dir))

        if min_confidence > 0:
            filtered = []
            for r in scan_results.get('results', []):
                kept = [f for f in r.findings if f.get('confidence', 0) >= min_confidence]
                if kept:
                    new_r = type(r)(
                        file_path=r.file_path,
                        findings=kept,
                        scan_time=r.scan_time,
                        file_size=r.file_size,
                        language=r.language,
                    )
                    filtered.append(new_r)
            scan_results['results'] = filtered

        serializer = _serialize_scan_results_to_json or _local_serialize
        payload_json = serializer(scan_results)

        return app.response_class(response=payload_json, status=200, mimetype="application/json")
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if repo_dir:
            try:
                shutil.rmtree(repo_dir, ignore_errors=True)
            except Exception:
                pass


@app.route('/<path:_any>', methods=["GET", "POST"], strict_slashes=False)
def catch_all(_any: str):
    """Fallback route to ensure serverless path prefix mismatches don't 404."""
    return scan_handler()


