"""Abstract Syntax Tree (AST) Security Filter and Static Code Analyzer for Sandbox Scripts."""

from __future__ import annotations

import ast
from typing import ClassVar


class ASTSecurityError(Exception):
    """Raised when generated experiment code violates sandbox static security invariants."""

    def __init__(self, violations: list[str]) -> None:
        super().__init__(f"AST Security Violation(s): {'; '.join(violations)}")
        self.violations = violations


class ASTSecurityValidator:
    """Statically verifies Python scripts before execution in the isolated sandbox."""

    BANNED_MODULES: ClassVar[set[str]] = {
        "socket",
        "requests",
        "urllib",
        "urllib3",
        "http",
        "httpx",
        "aiohttp",
        "websocket",
        "ftplib",
        "smtplib",
        "subprocess",
        "pty",
        "multiprocessing",
        "threading",
        "ctypes",
        "shutil",
        "pickle",
        "shelve",
        "importlib",
    }

    BANNED_BUILTIN_CALLS: ClassVar[set[str]] = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "getattr",
        "setattr",
        "delattr",
    }

    BANNED_OS_ATTRIBUTES: ClassVar[set[str]] = {
        "system",
        "popen",
        "remove",
        "unlink",
        "rmdir",
        "kill",
        "chmod",
        "chown",
        "rename",
        "replace",
        "execv",
        "execve",
        "spawn",
    }

    @classmethod
    def validate(cls, source_code: str) -> tuple[bool, list[str]]:
        """Validate source code. Returns (is_valid, list_of_violations)."""
        violations: list[str] = []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return False, [f"Syntax Error: {e}"]

        for node in ast.walk(tree):
            # 1. Check Import statements
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in cls.BANNED_MODULES:
                        violations.append(f"Banned module import '{alias.name}' (line {node.lineno})")

            # 2. Check ImportFrom statements
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in cls.BANNED_MODULES:
                        violations.append(f"Banned from-import from module '{node.module}' (line {node.lineno})")
                    if root_mod == "os":
                        for alias in node.names:
                            if alias.name in cls.BANNED_OS_ATTRIBUTES:
                                violations.append(f"Banned from-import of 'os.{alias.name}' (line {node.lineno})")

            # 3. Check Function / Call names
            elif isinstance(node, ast.Call):
                # Direct call like eval() or exec() or system()
                if isinstance(node.func, ast.Name):
                    if node.func.id in cls.BANNED_BUILTIN_CALLS:
                        violations.append(f"Banned builtin function call '{node.func.id}()' (line {node.lineno})")
                    elif node.func.id in cls.BANNED_OS_ATTRIBUTES:
                        violations.append(f"Banned dangerous function call '{node.func.id}()' (line {node.lineno})")

                # Attribute call like os.system() or obj.__subclasses__()
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name == "__subclasses__":
                        violations.append(f"Banned introspection call '__subclasses__()' (line {node.lineno})")

                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                        if attr_name in cls.BANNED_OS_ATTRIBUTES:
                            violations.append(f"Banned OS operation 'os.{attr_name}()' (line {node.lineno})")

            # 4. Check dangerous attribute access
            elif isinstance(node, ast.Attribute):
                if node.attr in {"__subclasses__", "__builtins__", "__globals__"}:
                    violations.append(f"Banned dangerous attribute access '{node.attr}' (line {node.lineno})")

        return len(violations) == 0, violations

    @classmethod
    def assert_valid(cls, source_code: str) -> None:
        """Asserts validity and raises ASTSecurityError if any violations exist."""
        is_valid, violations = cls.validate(source_code)
        if not is_valid:
            raise ASTSecurityError(violations)
