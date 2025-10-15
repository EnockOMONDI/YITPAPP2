#!/usr/bin/env python3
"""
Search for YITP Text Visibility Issues
Find all instances where YITP colors are used as backgrounds and check for proper white text contrast
"""

import os
import re
import glob
from pathlib import Path

class YITPTextVisibilityChecker:
    def __init__(self):
        self.yitp_colors = ['#ff5d15', '#1a2e53']
        self.issues = []
        self.fixes_applied = []
        
    def search_files(self, pattern, directory='.'):
        """Search for files matching pattern"""
        return glob.glob(os.path.join(directory, pattern), recursive=True)
    
    def check_file_for_yitp_backgrounds(self, file_path):
        """Check a file for YITP background usage and text contrast issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            issues_found = []
            
            # Pattern 1: Direct background color usage
            bg_patterns = [
                r'background[^;]*#ff5d15[^;]*;',
                r'background[^;]*#1a2e53[^;]*;',
                r'background-color[^;]*#ff5d15[^;]*;',
                r'background-color[^;]*#1a2e53[^;]*;',
                r'background[^;]*linear-gradient[^;]*#ff5d15[^;]*#1a2e53[^;]*;',
                r'background[^;]*linear-gradient[^;]*#1a2e53[^;]*#ff5d15[^;]*;'
            ]
            
            for pattern in bg_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Get surrounding context to check for text color
                    start = max(0, match.start() - 200)
                    end = min(len(content), match.end() + 200)
                    context = content[start:end]
                    
                    # Check if white text is specified
                    has_white_text = any(indicator in context.lower() for indicator in [
                        'color: white', 'color:#ffffff', 'color: #fff', 'color:#fff',
                        'text-white', 'color: #ffffff'
                    ])
                    
                    if not has_white_text:
                        line_num = content[:match.start()].count('\n') + 1
                        issues_found.append({
                            'file': file_path,
                            'line': line_num,
                            'issue': 'YITP background without white text',
                            'match': match.group(),
                            'context': context.strip()
                        })
            
            # Pattern 2: CSS class usage with YITP colors
            class_patterns = [
                r'class="[^"]*btn-primary[^"]*"',
                r'class="[^"]*bg-primary[^"]*"',
                r'class="[^"]*yitp[^"]*"'
            ]
            
            for pattern in class_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Check if this element or parent has text-white class
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]
                    
                    has_white_text_class = 'text-white' in context
                    
                    if not has_white_text_class and ('btn-primary' in match.group() or 'bg-primary' in match.group()):
                        line_num = content[:match.start()].count('\n') + 1
                        issues_found.append({
                            'file': file_path,
                            'line': line_num,
                            'issue': 'YITP class without text-white',
                            'match': match.group(),
                            'context': context.strip()
                        })
            
            return issues_found
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
    
    def scan_all_files(self):
        """Scan all relevant files for YITP text visibility issues"""
        print("🔍 SCANNING FOR YITP TEXT VISIBILITY ISSUES")
        print("=" * 60)
        
        # File patterns to search
        file_patterns = [
            'templates/**/*.html',
            'static/**/*.css',
            '**/*.py'  # For any inline styles in Python files
        ]
        
        all_files = []
        for pattern in file_patterns:
            all_files.extend(self.search_files(pattern))
        
        # Remove duplicates and filter relevant files
        unique_files = list(set(all_files))
        relevant_files = [f for f in unique_files if any(ext in f for ext in ['.html', '.css', '.py'])]
        
        print(f"📁 Scanning {len(relevant_files)} files...")
        
        total_issues = 0
        files_with_issues = 0
        
        for file_path in relevant_files:
            issues = self.check_file_for_yitp_backgrounds(file_path)
            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                self.issues.extend(issues)
                
                print(f"\n📄 {file_path}")
                for issue in issues:
                    print(f"   ⚠️  Line {issue['line']}: {issue['issue']}")
                    print(f"      Match: {issue['match'][:100]}...")
        
        print(f"\n📊 SCAN RESULTS:")
        print(f"   Files scanned: {len(relevant_files)}")
        print(f"   Files with issues: {files_with_issues}")
        print(f"   Total issues found: {total_issues}")
        
        return self.issues
    
    def generate_fixes(self):
        """Generate fixes for identified issues"""
        print(f"\n🔧 GENERATING FIXES FOR {len(self.issues)} ISSUES")
        print("=" * 50)
        
        fixes = {}
        
        for issue in self.issues:
            file_path = issue['file']
            if file_path not in fixes:
                fixes[file_path] = []
            
            if 'without white text' in issue['issue']:
                # CSS fix: add color: white
                fix = {
                    'line': issue['line'],
                    'type': 'css_color',
                    'description': 'Add color: white to YITP background element',
                    'original': issue['match'],
                    'suggested': issue['match'] + ' color: white;'
                }
            elif 'without text-white' in issue['issue']:
                # HTML fix: add text-white class
                fix = {
                    'line': issue['line'],
                    'type': 'html_class',
                    'description': 'Add text-white class to YITP background element',
                    'original': issue['match'],
                    'suggested': issue['match'].replace('"', ' text-white"')
                }
            else:
                fix = {
                    'line': issue['line'],
                    'type': 'manual',
                    'description': 'Manual review required',
                    'original': issue['match'],
                    'suggested': 'Review and add appropriate white text styling'
                }
            
            fixes[file_path].append(fix)
        
        return fixes
    
    def create_global_css_rule(self):
        """Create a global CSS rule to ensure white text on YITP backgrounds"""
        css_rule = """
/* YITP Text Visibility Fix - Global Rule */
/* Ensure all text on YITP colored backgrounds is white */
[style*="#ff5d15"], 
[style*="#1a2e53"],
.bg-primary,
.btn-primary,
.badge-primary,
[class*="yitp"][class*="bg"] {
    color: white !important;
}

/* Specific YITP gradient backgrounds */
[style*="linear-gradient"][style*="#ff5d15"],
[style*="linear-gradient"][style*="#1a2e53"] {
    color: white !important;
}

/* YITP button text visibility */
.btn-primary-yitp,
.btn-secondary-yitp {
    color: white !important;
}

/* YITP card headers and badges */
.yitp-card-header,
.yitp-badge,
.yitp-alert {
    color: white !important;
}
"""
        return css_rule
    
    def run_complete_scan(self):
        """Run complete scan and generate report"""
        print("🚀 YITP TEXT VISIBILITY CHECKER")
        print("=" * 60)
        
        # Scan for issues
        issues = self.scan_all_files()
        
        # Generate fixes
        fixes = self.generate_fixes()
        
        # Create global CSS rule
        global_css = self.create_global_css_rule()
        
        print(f"\n📋 SUMMARY REPORT")
        print("=" * 30)
        print(f"Issues found: {len(issues)}")
        print(f"Files affected: {len(fixes)}")
        
        if issues:
            print(f"\n🔧 RECOMMENDED ACTIONS:")
            print("1. Apply the global CSS rule below")
            print("2. Review and fix individual instances")
            print("3. Test all YITP branded elements")
            
            print(f"\n📝 GLOBAL CSS RULE TO ADD:")
            print(global_css)
            
            print(f"\n📄 DETAILED FIXES BY FILE:")
            for file_path, file_fixes in fixes.items():
                print(f"\n{file_path}:")
                for fix in file_fixes:
                    print(f"   Line {fix['line']}: {fix['description']}")
        else:
            print("✅ No text visibility issues found!")
        
        return {
            'issues': issues,
            'fixes': fixes,
            'global_css': global_css
        }

if __name__ == "__main__":
    checker = YITPTextVisibilityChecker()
    results = checker.run_complete_scan()
