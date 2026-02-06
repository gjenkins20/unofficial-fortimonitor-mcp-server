#!/usr/bin/env python3
"""
Automatic Tool Definition Fixer
Converts dict-based tool definitions to Tool object-based definitions.
"""

import re
from pathlib import Path

def fix_tool_file(file_path: Path) -> bool:
    """Fix a single tool definition file.
    
    Args:
        file_path: Path to the tool definition file
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    print(f"Processing: {file_path}")
    
    # Read file
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Check if already has Tool import
    has_tool_import = 'from mcp.types import Tool' in content or 'from mcp import types' in content
    
    # Add import if needed
    if not has_tool_import:
        # Find the last import line
        import_pattern = r'^(from .+ import .+|import .+)$'
        matches = list(re.finditer(import_pattern, content, re.MULTILINE))
        
        if matches:
            # Add after last import
            last_import = matches[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + '\nfrom mcp.types import Tool' + content[insert_pos:]
            print("  ✓ Added Tool import")
        else:
            # Add at beginning
            content = 'from mcp.types import Tool\n\n' + content
            print("  ✓ Added Tool import at beginning")
    
    # Fix function return type annotations
    # Pattern: def function_name(...) -> dict:
    def_pattern = r'(def \w+_tool_definition\([^)]*\))\s*->\s*dict\s*:'
    
    def replace_return_type(match):
        return match.group(1) + ' -> Tool:'
    
    new_content = re.sub(def_pattern, replace_return_type, content)
    if new_content != content:
        print("  ✓ Fixed return type annotations (dict -> Tool)")
        content = new_content
    
    # Fix return statements
    # This is more complex as we need to match the entire dict structure
    # Pattern: return { ... }
    # We'll use a simple approach: find "return {" and replace with "return Tool("
    # Then find the matching closing "}" and replace with ")"
    
    # Split into lines for easier processing
    lines = content.split('\n')
    modified = False
    in_return_dict = False
    brace_count = 0
    
    for i, line in enumerate(lines):
        # Check for start of return dict
        if re.search(r'return\s*\{', line) and '_tool_definition' in ''.join(lines[max(0, i-10):i+1]):
            # Replace return { with return Tool(
            lines[i] = re.sub(r'return\s*\{', 'return Tool(', line)
            in_return_dict = True
            brace_count = 1
            modified = True
            continue
        
        # Track brace count if in return dict
        if in_return_dict:
            brace_count += line.count('{') - line.count('}')
            
            # If we've closed all braces, replace last } with )
            if brace_count == 0:
                # Find last } and replace with )
                if '}' in line:
                    # Replace only the closing brace of the dict, not any inner ones
                    lines[i] = line[::-1].replace('}', ')', 1)[::-1]
                in_return_dict = False
    
    if modified:
        print("  ✓ Fixed return statements (return {...} -> return Tool(...))")
        content = '\n'.join(lines)
    
    # Write back if changed
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Updated: {file_path.name}")
        return True
    else:
        print(f"  ⏭️  No changes needed: {file_path.name}")
        return False

def main():
    """Main function to fix all tool definition files."""
    print("=" * 60)
    print("FortiMonitor MCP - Tool Definition Fixer")
    print("=" * 60)
    print()
    
    # Find project root (assuming script is run from project root)
    project_root = Path.cwd()
    tools_dir = project_root / 'src' / 'tools'
    
    if not tools_dir.exists():
        print(f"❌ Error: Tools directory not found: {tools_dir}")
        print("   Please run this script from the project root directory.")
        return 1
    
    print(f"Tools directory: {tools_dir}")
    print()
    
    # Find all Python files in tools directory
    tool_files = list(tools_dir.glob('*.py'))
    tool_files = [f for f in tool_files if f.name != '__init__.py']
    
    if not tool_files:
        print("❌ No tool files found!")
        return 1
    
    print(f"Found {len(tool_files)} tool files:")
    for f in tool_files:
        print(f"  - {f.name}")
    print()
    
    # Process each file
    modified_count = 0
    for tool_file in tool_files:
        try:
            if fix_tool_file(tool_file):
                modified_count += 1
            print()
        except Exception as e:
            print(f"  ❌ Error processing {tool_file.name}: {e}")
            print()
    
    # Summary
    print("=" * 60)
    print(f"Summary:")
    print(f"  Files processed: {len(tool_files)}")
    print(f"  Files modified: {modified_count}")
    print(f"  Files unchanged: {len(tool_files) - modified_count}")
    print()
    
    if modified_count > 0:
        print("✅ Tool definitions fixed!")
        print()
        print("Next steps:")
        print("  1. Review the changes: git diff src/tools/")
        print("  2. Rebuild image: docker build -t fortimonitor-mcp:latest .")
        print("  3. Test container: docker run -d --name test -e FORTIMONITOR_API_KEY=key fortimonitor-mcp:latest")
        print("  4. Verify with Claude")
    else:
        print("ℹ️  All files already correct or no changes needed.")
    
    print("=" * 60)
    return 0

if __name__ == '__main__':
    exit(main())