#!/usr/bin/env python3
"""
YITP PI Training Conversion - Complete Workflow
Orchestrates the entire process of converting PI Training PowerPoint files to Module 2 JSON

Usage:
python run_pi_training_conversion.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


class PITrainingConverter:
    """Orchestrates the complete PI Training conversion workflow"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.pi_directory = self.project_root / "PI"
        self.output_file = self.project_root / "pi_training_module2.json"
        self.log_file = self.project_root / "conversion_log.txt"
        
        # Expected PI Training files
        self.expected_files = [
            "Batch 1 PI Training Editing Version SLIDES 1-9 ENGLISH (1).pptx",
            "Batch 2 PI Training Editing Version SLIDES 10 - 20 ENGLISH (1).pptx", 
            "BATCH 3 PI Training Editing Slides 21 - 31 ENGLISH (2).pptx",
            "BATCH 5 PI Training Editing Slides 40 - 55 - with MO Edits added by SP.pptx",
            "BATCH 6 PI Training editing SLIDES 56 - 71.pptx",
            "Batch 8 PI Training Editing Slides 83 - 91.pptx",
            "Batch 9 PI Training Editing Slides 92 - 108.pptx",
            "Batch 10 PI Training Slides 109 - 121.pptx"
        ]
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.log("🔍 Checking prerequisites...")
        
        # Check if PI directory exists
        if not self.pi_directory.exists():
            self.log(f"❌ PI directory not found: {self.pi_directory}", "ERROR")
            self.log("💡 Please create the PI directory and place PowerPoint files there", "INFO")
            return False
        
        # Check for PowerPoint files
        pptx_files = list(self.pi_directory.glob("*.pptx"))
        if not pptx_files:
            self.log("❌ No PowerPoint files found in PI directory", "ERROR")
            self.log("💡 Please place the PI Training PowerPoint files in the PI directory", "INFO")
            return False
        
        self.log(f"✅ Found {len(pptx_files)} PowerPoint files")
        
        # List found files
        for file in pptx_files:
            self.log(f"   📄 {file.name}")
        
        # Check for missing expected files
        found_names = [f.name for f in pptx_files]
        missing_files = [f for f in self.expected_files if f not in found_names]
        
        if missing_files:
            self.log("⚠️ Some expected files are missing:", "WARNING")
            for missing in missing_files:
                self.log(f"   ❓ {missing}", "WARNING")
        
        # Check Python dependencies
        try:
            import pptx
            self.log("✅ python-pptx is available")
        except ImportError:
            self.log("❌ python-pptx not installed", "ERROR")
            self.log("💡 Install with: pip install python-pptx", "INFO")
            return False
        
        try:
            import pdfplumber
            self.log("✅ pdfplumber is available")
        except ImportError:
            self.log("⚠️ pdfplumber not installed (PDF processing disabled)", "WARNING")
        
        try:
            from bs4 import BeautifulSoup
            self.log("✅ beautifulsoup4 is available")
        except ImportError:
            self.log("⚠️ beautifulsoup4 not installed (HTML processing limited)", "WARNING")
        
        return True
    
    def run_content_extraction(self) -> bool:
        """Run the content extraction script"""
        self.log("🚀 Starting content extraction...")
        
        try:
            # Run the content extraction script
            cmd = [
                sys.executable, 
                "content_extraction_system.py",
                "--input-dir", str(self.pi_directory),
                "--output-file", str(self.output_file),
                "--lessons", "6"
            ]
            
            self.log(f"📝 Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log("✅ Content extraction completed successfully")
                self.log("📄 Output saved to: " + str(self.output_file))
                return True
            else:
                self.log("❌ Content extraction failed", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error running content extraction: {str(e)}", "ERROR")
            return False
    
    def validate_output(self) -> bool:
        """Validate the generated JSON output"""
        self.log("🔍 Validating generated JSON...")
        
        if not self.output_file.exists():
            self.log("❌ Output file not found", "ERROR")
            return False
        
        try:
            # Run JSON validation
            cmd = [
                sys.executable,
                "json_schema_validator.py", 
                "--input", str(self.output_file),
                "--verbose"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            self.log("📋 Validation Results:")
            self.log(result.stdout)
            
            if "✅ VALID" in result.stdout:
                self.log("✅ JSON validation passed")
                return True
            else:
                self.log("⚠️ JSON validation found issues", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Error running validation: {str(e)}", "ERROR")
            return False
    
    def generate_summary_report(self) -> None:
        """Generate a summary report of the conversion"""
        self.log("📊 Generating summary report...")
        
        try:
            if self.output_file.exists():
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract statistics
                total_modules = len(data.get('modules', []))
                total_lessons = 0
                total_questions = 0
                total_duration = 0
                
                for module in data.get('modules', []):
                    lessons = module.get('lessons', [])
                    total_lessons += len(lessons)
                    
                    for lesson in lessons:
                        total_duration += lesson.get('estimated_duration', 0)
                        
                        assessment = lesson.get('assessment', {})
                        if 'quiz' in assessment:
                            quiz = assessment['quiz']
                            total_questions += len(quiz.get('questions', []))
                
                # Generate report
                report = f"""
📋 PI TRAINING CONVERSION SUMMARY REPORT
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📚 COURSE INFORMATION:
   Title: {data.get('course_title', 'N/A')}
   Category: {data.get('course_category', 'N/A')}
   Price: ${data.get('price', 0)} {data.get('currency', 'USD')}
   Status: {data.get('status', 'N/A')}

📊 CONTENT STATISTICS:
   Modules: {total_modules}
   Lessons: {total_lessons}
   Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)
   Quiz Questions: {total_questions}
   Avg Questions/Lesson: {total_questions/total_lessons:.1f}

📁 FILES PROCESSED:
   Input Directory: {self.pi_directory}
   Output File: {self.output_file}
   File Size: {self.output_file.stat().st_size / 1024:.1f} KB

🎯 NEXT STEPS:
   1. Review the generated JSON content
   2. Upload any referenced files to Uploadcare
   3. Update resource URLs in the JSON
   4. Import into YITP LMS for testing
   5. Verify trial system integration

✅ CONVERSION COMPLETED SUCCESSFULLY!
"""
                
                self.log(report)
                
                # Save report to file
                report_file = self.project_root / "conversion_summary_report.txt"
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                self.log(f"📄 Summary report saved to: {report_file}")
                
        except Exception as e:
            self.log(f"❌ Error generating summary report: {str(e)}", "ERROR")
    
    def run_complete_workflow(self) -> bool:
        """Run the complete conversion workflow"""
        self.log("🚀 Starting PI Training Conversion Workflow")
        self.log("="*60)
        
        # Initialize log file
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"PI Training Conversion Log - {datetime.now().isoformat()}\n")
            f.write("="*60 + "\n")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.log("❌ Prerequisites check failed. Aborting.", "ERROR")
            return False
        
        # Step 2: Run content extraction
        if not self.run_content_extraction():
            self.log("❌ Content extraction failed. Aborting.", "ERROR")
            return False
        
        # Step 3: Validate output
        validation_passed = self.validate_output()
        
        # Step 4: Generate summary report
        self.generate_summary_report()
        
        # Final status
        if validation_passed:
            self.log("🎉 PI Training conversion completed successfully!")
            self.log(f"📁 Output file: {self.output_file}")
            self.log(f"📋 Log file: {self.log_file}")
            return True
        else:
            self.log("⚠️ Conversion completed with validation warnings", "WARNING")
            self.log("🔧 Please review and fix any issues before importing to YITP LMS", "WARNING")
            return False


def main():
    """Main function"""
    print("🎯 YITP PI Training Conversion System")
    print("="*50)
    print("Converting PowerPoint files to Module 2 JSON...")
    print()
    
    converter = PITrainingConverter()
    success = converter.run_complete_workflow()
    
    if success:
        print("\n🎉 SUCCESS! PI Training Module 2 is ready for YITP LMS integration.")
        print("\n📋 Next Steps:")
        print("   1. Review the generated JSON file")
        print("   2. Upload any media files to Uploadcare")
        print("   3. Update resource URLs in the JSON")
        print("   4. Import into YITP LMS")
        print("   5. Test trial system integration")
    else:
        print("\n❌ CONVERSION FAILED or completed with issues.")
        print("   Please check the log file for details and fix any problems.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
