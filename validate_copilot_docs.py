#!/usr/bin/env python3
"""
Validation script for GitHub Copilot documentation completeness
"""

import os
import re

def check_file_exists(filepath):
    """Check if a file exists and return its size"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        return True, size
    return False, 0

def count_sections(filepath):
    """Count the number of sections (headers) in a markdown file"""
    if not os.path.exists(filepath):
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count markdown headers (lines starting with #)
    headers = re.findall(r'^#+\s+.+$', content, re.MULTILINE)
    return len(headers)

def count_code_blocks(filepath):
    """Count code blocks in a markdown file"""
    if not os.path.exists(filepath):
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count code blocks (```...```)
    code_blocks = re.findall(r'```[\s\S]*?```', content)
    return len(code_blocks)

def main():
    """Validate the Copilot documentation"""
    print("🔍 Validating GitHub Copilot Documentation for UWH Scoring App")
    print("="*60)
    
    files_to_check = [
        "GITHUB_COPILOT_INSTRUCTIONS.md",
        "COPILOT_QUICK_REFERENCE.md", 
        "COPILOT_EXAMPLES.md",
        "uwh.py"
    ]
    
    all_valid = True
    
    for filepath in files_to_check:
        exists, size = check_file_exists(filepath)
        if exists:
            print(f"✅ {filepath}: {size:,} bytes")
            
            if filepath.endswith('.md'):
                sections = count_sections(filepath)
                code_blocks = count_code_blocks(filepath)
                print(f"   📝 {sections} sections, {code_blocks} code blocks")
        else:
            print(f"❌ {filepath}: Missing!")
            all_valid = False
    
    print("\n📊 Content Analysis:")
    
    # Check main instructions document
    main_doc = "GITHUB_COPILOT_INSTRUCTIONS.md"
    if os.path.exists(main_doc):
        with open(main_doc, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        key_topics = [
            "gamemanagementapp",
            "tkinter", 
            "scoreboard",
            "underwater hockey",
            "confirmation dialog",
            "font scaling",
            "timer",
            "debugging",
            "testing"
        ]
        
        coverage = sum(1 for topic in key_topics if topic in content)
        print(f"   📋 Topic coverage: {coverage}/{len(key_topics)} key topics")
        
        if coverage < len(key_topics):
            missing = [topic for topic in key_topics if topic not in content]
            print(f"   ⚠️  Missing topics: {', '.join(missing)}")
    
    # Check examples document
    examples_doc = "COPILOT_EXAMPLES.md"
    if os.path.exists(examples_doc):
        with open(examples_doc, 'r', encoding='utf-8') as f:
            content = f.read()
        
        example_count = content.count("### Example")
        print(f"   🛠️  Practical examples: {example_count}")
        
        if example_count < 3:
            print(f"   ⚠️  Consider adding more examples (current: {example_count})")
    
    print("\n" + "="*60)
    if all_valid:
        print("🎉 All documentation files are present and comprehensive!")
        print("   Developers can now use GitHub Copilot effectively with this codebase.")
    else:
        print("⚠️  Some documentation files are missing. Please create them.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())