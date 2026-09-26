"""Code diff generator for fix suggestions."""
import difflib
from typing import Optional, Tuple


class DiffGenerator:
    """Generates unified diffs for code changes."""
    
    def generate_diff(
        self,
        old_content: str,
        new_content: str,
        file_path: str = "file"
    ) -> str:
        """
        Generate a unified diff between two code versions.
        
        Args:
            old_content: Original code
            new_content: Modified code
            file_path: Path to the file
            
        Returns:
            Unified diff string
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="\n"
        )

        # difflib leaves unterminated source lines as-is. Give every patch
        # record its own line and preserve the missing final newline explicitly.
        return ''.join(
            line if line.endswith('\n') else line + '\n\\ No newline at end of file\n'
            for line in diff
        )
    
    def apply_fix(
        self,
        source: str,
        line_start: int,
        line_end: int,
        replacement: str
    ) -> Tuple[str, str]:
        """
        Apply a fix by replacing lines in source code.
        
        Args:
            source: Original source code
            line_start: Start line (1-indexed)
            line_end: End line (1-indexed)
            replacement: New code to insert
            
        Returns:
            Tuple of (new_source, diff)
        """
        lines = source.splitlines(keepends=True)
        
        # Adjust for 0-indexing
        start_idx = line_start - 1
        end_idx = line_end
        
        # Create new content
        new_lines = (
            lines[:start_idx] +
            [replacement + '\n'] +
            lines[end_idx:]
        )
        
        new_source = ''.join(new_lines)
        diff = self.generate_diff(source, new_source)
        
        return new_source, diff
    
    def add_import(
        self,
        source: str,
        import_statement: str
    ) -> Tuple[str, str]:
        """
        Add an import statement to the source.
        
        Args:
            source: Original source code
            import_statement: Import to add
            
        Returns:
            Tuple of (new_source, diff)
        """
        lines = source.splitlines(keepends=True)
        
        # Find last import line
        last_import_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                last_import_idx = i + 1
        
        # Insert after last import
        new_lines = (
            lines[:last_import_idx] +
            [import_statement + '\n'] +
            lines[last_import_idx:]
        )
        
        new_source = ''.join(new_lines)
        diff = self.generate_diff(source, new_source)
        
        return new_source, diff
    
    def add_fixture(
        self,
        source: str,
        fixture_code: str
    ) -> Tuple[str, str]:
        """
        Add a pytest fixture to the test class/module.
        
        Args:
            source: Original source code
            fixture_code: Fixture code to add
            
        Returns:
            Tuple of (new_source, diff)
        """
        lines = source.splitlines(keepends=True)
        
        # Find class definition or first test function
        insert_idx = 0
        for i, line in enumerate(lines):
            if 'class Test' in line or line.strip().startswith('def test_'):
                insert_idx = i
                break
        
        # Insert fixture
        new_lines = (
            lines[:insert_idx] +
            [fixture_code + '\n\n'] +
            lines[insert_idx:]
        )
        
        new_source = ''.join(new_lines)
        diff = self.generate_diff(source, new_source)
        
        return new_source, diff
