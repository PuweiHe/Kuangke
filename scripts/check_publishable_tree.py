"""Check the public working tree for common private data and adapter identities."""

import ast
import ipaddress
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', '.venv', '__pycache__', '.pytest_cache', 'work'}
SKIP_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.ico', '.pyc'}
PATTERNS = {
    'private key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'provider key': r'\bsk-[A-Za-z0-9_-]{16,}',
    'personal home path': r'/(?:Users|home)/[A-Za-z0-9_.-]+/',
    'credential URL': r'[a-z]+://[^\s/:]+:[^\s/@]+@',
}
IDENTITY_FIELDS = {'userId', 'user_id', 'user_code'}


def has_literal_identity(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and key.value in IDENTITY_FIELDS
                        and isinstance(value, ast.Constant)
                        and str(value.value).isdigit() and len(str(value.value)) >= 4):
                    return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = [arg.arg for arg in node.args.args][-len(node.args.defaults):]
            for name, value in zip(names, node.args.defaults):
                if (name in IDENTITY_FIELDS and isinstance(value, ast.Constant)
                        and str(value.value).isdigit() and len(str(value.value)) >= 4):
                    return True
    return False


def inspect():
    findings = set()
    listed = subprocess.run(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout.decode().split('\0')
    for name in filter(None, listed):
        path = ROOT / name
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        rel = str(path.relative_to(ROOT))
        if path.name == '.env' or path.suffix in {'.pem', '.key', '.xlsx', '.xls', '.log'}:
            findings.add((rel, 'excluded file type'))
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        try:
            content = path.read_text()
        except (OSError, UnicodeDecodeError):
            findings.add((rel, 'unreviewed binary'))
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                findings.add((rel, label))
        for domain in re.findall(r'[\w.+-]+@([\w.-]+\.[A-Za-z]{2,})', content):
            if domain not in {'example.com', 'example.invalid'}:
                findings.add((rel, 'email address'))
        for value in re.findall(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])', content):
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                continue
            if not address.is_loopback and not address.is_unspecified:
                findings.add((rel, 'nonlocal IP address'))
        if path.suffix == '.py':
            try:
                tree = ast.parse(content)
            except SyntaxError:
                findings.add((rel, 'Python syntax error'))
            else:
                if has_literal_identity(tree):
                    findings.add((rel, 'hardcoded user identifier'))
    return sorted(findings)


if __name__ == '__main__':
    findings = inspect()
    for path, reason in findings:
        print(f'{path}: {reason}')
    print(f'Publishable tree findings: {len(findings)}')
    sys.exit(bool(findings))
