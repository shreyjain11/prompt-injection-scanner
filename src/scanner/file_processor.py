"""
File processing utilities for the scanner.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
import mimetypes


class FileProcessor:
    """Handles file reading and language detection."""
    
    # File extensions to scan
    SCANNABLE_EXTENSIONS = {
        # Programming languages
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php',
        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.dart', '.r', '.m', '.mm',
        # Web technologies
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        # Configuration files
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config',
        '.env', '.properties', '.xml', '.csv',
        # Documentation
        '.md', '.txt', '.rst', '.adoc',
        # Shell scripts
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        # Other
        '.sql', '.graphql', '.gql', '.proto', '.thrift'
    }
    
    # Binary file extensions to skip
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.db', '.sqlite',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.pdf',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2', '.xz',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.class', '.o', '.obj', '.a', '.lib'
    }
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': [r'\.py$', r'#!/usr/bin/env python', r'#!/usr/bin/python'],
        'javascript': [r'\.js$', r'#!/usr/bin/env node', r'#!/usr/bin/node'],
        'typescript': [r'\.ts$', r'\.tsx$'],
        'java': [r'\.java$', r'public class', r'package '],
        'cpp': [r'\.cpp$', r'\.cc$', r'\.cxx$', r'#include <'],
        'c': [r'\.c$', r'#include <'],
        'php': [r'\.php$', r'<?php', r'#!/usr/bin/env php'],
        'ruby': [r'\.rb$', r'#!/usr/bin/env ruby', r'#!/usr/bin/ruby'],
        'go': [r'\.go$', r'package main', r'import '],
        'rust': [r'\.rs$', r'use ', r'fn main'],
        'swift': [r'\.swift$', r'import ', r'func '],
        'kotlin': [r'\.kt$', r'package ', r'fun '],
        'scala': [r'\.scala$', r'package ', r'object '],
        'dart': [r'\.dart$', r'import ', r'void main'],
        'r': [r'\.r$', r'library\(', r'require\('],
        'html': [r'\.html$', r'\.htm$', r'<!DOCTYPE html>', r'<html'],
        'css': [r'\.css$', r'\.scss$', r'\.sass$', r'\.less$'],
        'vue': [r'\.vue$', r'<template>', r'<script>'],
        'svelte': [r'\.svelte$', r'<script>', r'<style>'],
        'json': [r'\.json$'],
        'yaml': [r'\.yaml$', r'\.yml$'],
        'toml': [r'\.toml$'],
        'xml': [r'\.xml$', r'<?xml'],
        'sql': [r'\.sql$', r'SELECT ', r'INSERT ', r'UPDATE ', r'DELETE '],
        'graphql': [r'\.graphql$', r'\.gql$', r'query ', r'mutation '],
        'shell': [r'\.sh$', r'\.bash$', r'\.zsh$', r'#!/bin/bash', r'#!/bin/sh'],
        'powershell': [r'\.ps1$', r'#!/usr/bin/env pwsh', r'param\('],
        'batch': [r'\.bat$', r'\.cmd$', r'@echo off', r'set '],
        'markdown': [r'\.md$', r'\.markdown$'],
        'text': [r'\.txt$', r'\.rst$', r'\.adoc$']
    }
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):  # 10MB default
        self.max_file_size = max_file_size
        self._compiled_patterns = {
            lang: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for lang, patterns in self.LANGUAGE_PATTERNS.items()
        }
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read a file and return its content as a string.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string, or None if file cannot be read
        """
        try:
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                return None
            
            # Check if it's a binary file
            if self._is_binary_file(file_path):
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return content
            
        except (IOError, OSError, UnicodeDecodeError):
            return None
    
    def detect_language(self, file_path: Path, content: str) -> Optional[str]:
        """
        Detect the programming language of a file.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Detected language name, or None if unknown
        """
        # First check by file extension
        extension = file_path.suffix.lower()
        
        # Direct extension mapping
        extension_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.dart': 'dart',
            '.r': 'r',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.vue': 'vue',
            '.svelte': 'svelte',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.xml': 'xml',
            '.sql': 'sql',
            '.graphql': 'graphql',
            '.gql': 'graphql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.zsh': 'shell',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.md': 'markdown',
            '.txt': 'text',
            '.rst': 'text',
            '.adoc': 'text'
        }
        
        if extension in extension_to_lang:
            return extension_to_lang[extension]
        
        # If no direct match, try pattern matching
        for language, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(content[:1000]):  # Check first 1000 chars
                    return language
        
        return None
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary."""
        # Check extension first
        if file_path.suffix.lower() in self.BINARY_EXTENSIONS:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and not mime_type.startswith('text/'):
            return True
        
        # Check file content (first 1024 bytes)
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return True
                # Check if mostly printable ASCII
                printable = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in (9, 10, 13))
                if len(chunk) > 0 and printable / len(chunk) < 0.7:
                    return True
        except:
            return True
        
        return False
    
    def is_scannable(self, file_path: Path) -> bool:
        """Check if a file should be scanned."""
        # Check extension
        if file_path.suffix.lower() in self.SCANNABLE_EXTENSIONS:
            return True
        
        # Check if it's a text file without extension
        if not file_path.suffix and self._is_text_file(file_path):
            return True
        
        return False
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file appears to be a text file."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                # Check for null bytes
                if b'\x00' in chunk:
                    return False
                # Check if mostly printable ASCII
                printable = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in (9, 10, 13))
                return len(chunk) > 0 and printable / len(chunk) >= 0.7
        except:
            return False





