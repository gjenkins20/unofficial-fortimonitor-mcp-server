#!/usr/bin/env python3
"""
FortiMonitor MCP - Careful Tool Definition Fixer
Only fixes Tool() parameters, preserves inputSchema dictionaries.
"""

import re
from pathlib import Path

def fix_file_content(content: str) -> tuple[str, list[str]]:
    """Fix tool definitions in file content.
    
    Returns:
        (fixed_content, list_of_changes)
    """
    changes = []
    original = content
    
    # Add Tool import if missing
    if 'from mcp.types import Tool' not in content and 'from mcp import types' not in content:
        # Find the last import line
        matches = list(re.finditer(r'^(?:from .+? import .+?|import .+?)$', content, re.MULTILINE))
        if matches:
            insert_pos = matches[-1].end()
            content = content[:insert_pos] + '\nfrom mcp.types import Tool' + content[insert_pos:]
            changes.append("Added Tool import")
    
    # Fix return type: -> dict: to -> Tool:
    new_content = re.sub(
        r'(\bdef\s+\w+_tool_definition\s*\([^)]*\))\s*->\s*dict\s*:',
        r'\1 -> Tool:',
        content
    )
    if new_content != content:
        changes.append("Fixed return type (dict → Tool)")
        content = new_content
    
    # Now the careful part: fix return statements
    # We need to change return { to return Tool( and fix only the top-level parameters
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a return statement with dict
        if re.search(r'return\s*\{', line):
            # This is the start of a return dict block
            # We need to:
            # 1. Change { to Tool(
            # 2. Find and fix the three top-level keys: name, description, inputSchema
            # 3. Change the final } to )
            
            # Collect all lines in this return block
            return_block = [line]
            brace_count = line.count('{') - line.count('}')
            i += 1
            
            while i < len(lines) and brace_count > 0:
                return_block.append(lines[i])
                brace_count += lines[i].count('{') - lines[i].count('}')
                i += 1
            
            # Now fix this block
            fixed_block = fix_return_block(return_block)
            fixed_lines.extend(fixed_block)
            
            if fixed_block != return_block:
                changes.append("Fixed Tool() parameters")
            
        else:
            fixed_lines.append(line)
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Remove duplicate changes
    changes = list(dict.fromkeys(changes))
    
    return content, changes

def fix_return_block(lines: list[str]) -> list[str]:
    """Fix a return block to use Tool() instead of dict.
    
    Only fixes the top-level keys: name, description, inputSchema.
    Preserves dictionary syntax inside inputSchema.
    """
    if not lines:
        return lines
    
    fixed = []
    
    # Track state
    depth = 0  # Brace depth
    in_inputschema = False  # Are we inside the inputSchema dict?
    
    for i, line in enumerate(lines):
        new_line = line
        
        # First line: change return { to return Tool(
        if i == 0:
            new_line = re.sub(r'return\s*\{', 'return Tool(', new_line)
        
        # Track brace depth BEFORE we process this line
        old_depth = depth
        depth += line.count('{') - line.count('}')
        
        # Check if we're entering inputSchema on this line
        if '"inputSchema"' in line and old_depth == 1:
            # This is the top-level inputSchema key
            new_line = re.sub(r'"inputSchema"\s*:', 'inputSchema=', new_line)
            in_inputschema = True
        
        # If we're at depth 1 (top level) and NOT in inputSchema yet
        elif old_depth == 1 and not in_inputschema:
            # Fix top-level name
            if re.match(r'\s*"name"\s*:', new_line):
                new_line = re.sub(r'"name"\s*:', 'name=', new_line)
            
            # Fix top-level description
            elif re.match(r'\s*"description"\s*:', new_line):
                new_line = re.sub(r'"description"\s*:', 'description=', new_line)
        
        # Check if we're exiting inputSchema
        if in_inputschema and depth == 1 and '}' in line:
            # We're closing the inputSchema dict
            in_inputschema = False
        
        fixed.append(new_line)
    
    # Last line: change final } to )
    if fixed:
        # Find the last line with } that closes the whole block
        for i in range(len(fixed) - 1, -1, -1):
            if '}' in fixed[i]:
                # Count braces to ensure this is the closing one
                total_open = sum(line.count('{') for line in fixed[:i+1])
                total_close = sum(line.count('}') for line in fixed[:i+1])
                
                if total_open == total_close:
                    # This is the final closing brace
                    # Replace the last } with )
                    fixed[i] = fixed[i][::-1].replace('}', ')', 1)[::-1]
                    break
    
    return fixed

def process_file(file_path: Path) -> bool:
    """Process a single file.
    
    Returns:
        True if file was modified
    """
    print(f"\n📄 {file_path.name}")
    
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed_content, changes = fix_file_content(content)
        
        if fixed_content != content:
            # Verify syntax before writing
            try:
                compile(fixed_content, str(file_path), 'exec')
            except SyntaxError as e:
                print(f"   ⚠️  Fix would create syntax error at line {e.lineno}: {e.msg}")
                print(f"   ⏭️  Skipping this file - manual fix required")
                return False
            
            # Write the fixed content
            file_path.write_text(fixed_content, encoding='utf-8')
            
            for change in changes:
                print(f"   ✓ {change}")
            
            return True
        else:
            print(f"   ⏭️  No changes needed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_syntax(file_path: Path) -> bool:
    """Verify file has valid Python syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), str(file_path), 'exec')
        return True
    except SyntaxError as e:
        print(f"   ❌ Line {e.lineno}: {e.msg}")
        if e.text:
            print(f"      {e.text.strip()}")
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("FortiMonitor MCP - Careful Tool Definition Fixer")
    print("=" * 70)
    print()
    print("This script will:")
    print("  • Add 'from mcp.types import Tool' imports")
    print("  • Change return type: -> dict: to -> Tool:")
    print("  • Change return { to return Tool(")
    print("  • Fix top-level parameters: name, description, inputSchema")
    print("  • Preserve dictionary syntax inside inputSchema")
    print()
    
    # Find tools directory
    tools_dir = Path('src/tools')
    
    if not tools_dir.exists():
        print(f"❌ Error: Directory not found: {tools_dir}")
        print("   Please run this script from the project root directory.")
        return 1
    
    print(f"📁 Tools directory: {tools_dir}")
    
    # Find all Python files
    files = [f for f in tools_dir.glob('*.py') if f.name != '__init__.py']
    
    if not files:
        print("\n❌ No tool files found!")
        return 1
    
    print(f"\n📚 Found {len(files)} tool files:")
    for f in sorted(files):
        print(f"   • {f.name}")
    
    # Process each file
    print("\n" + "=" * 70)
    print("Processing Files")
    print("=" * 70)
    
    modified_count = 0
    for file_path in sorted(files):
        if process_file(file_path):
            modified_count += 1
    
    # Verify all files
    print("\n" + "=" * 70)
    print("Verifying Syntax")
    print("=" * 70)
    
    all_valid = True
    for file_path in sorted(files):
        print(f"\n🔍 {file_path.name}")
        if verify_syntax(file_path):
            print(f"   ✅ Valid syntax")
        else:
            all_valid = False
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  Files processed: {len(files)}")
    print(f"  Files modified: {modified_count}")
    print(f"  Files unchanged: {len(files) - modified_count}")
    print(f"  All syntax valid: {'✅ Yes' if all_valid else '❌ No'}")
    
    if all_valid:
        print("\n✅ Success! All files have valid syntax.")
        print("\nNext steps:")
        print("  1. Review changes: git diff src/tools/")
        print("  2. Rebuild image: docker build -t fortimonitor-mcp:latest .")
        print("  3. Test container:")
        print("     docker run -d --name test -e FORTIMONITOR_API_KEY=key fortimonitor-mcp:latest")
        print("  4. Check logs: docker logs test")
        print("  5. Test with Claude Code")
    else:
        print("\n⚠️  Some files have syntax errors.")
        print("   Please review and fix manually, or check the error messages above.")
    
    print("=" * 70)
    
    return 0 if all_valid else 1

if __name__ == '__main__':
    exit(main())
