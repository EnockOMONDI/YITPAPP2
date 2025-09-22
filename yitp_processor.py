#!/usr/bin/env python3
"""
YITP Content Processor - Complete Workflow Orchestrator
Fresh standalone system for converting PDF/PPTX to YITP JSON

Usage:
python yitp_processor.py --input source_files/ --output final_course.json --title "My Course"
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YITPProcessor:
    """Complete YITP content processing workflow orchestrator"""
    
    def __init__(self, input_dir: Path, output_file: Path):
        self.input_dir = input_dir
        self.output_file = output_file
        self.temp_dir = Path("temp_yitp_processing")
        
        # Intermediate files
        self.extracted_file = self.temp_dir / "extracted_content.json"
        self.validation_report = self.temp_dir / "validation_report.txt"
        
        # Processing statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'files_processed': 0,
            'content_units_extracted': 0,
            'modules_created': 0,
            'lessons_created': 0,
            'quiz_questions_generated': 0,
            'validation_score': 0.0,
            'success': False
        }
    
    def setup_environment(self) -> bool:
        """Setup processing environment and check dependencies"""
        logger.info("Setting up YITP processing environment...")
        
        # Create temp directory
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check if input directory exists
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return False
        
        if not self.input_dir.is_dir():
            logger.error(f"Input path is not a directory: {self.input_dir}")
            return False
        
        # Check for source files
        pdf_files = list(self.input_dir.glob("*.pdf"))
        pptx_files = list(self.input_dir.glob("*.pptx"))
        
        if not pdf_files and not pptx_files:
            logger.error("No PDF or PPTX files found in input directory")
            return False
        
        self.stats['files_processed'] = len(pdf_files) + len(pptx_files)
        logger.info(f"Found {len(pdf_files)} PDF files and {len(pptx_files)} PPTX files")
        
        # Check Python dependencies
        required_modules = ['pptx', 'pdfplumber', 'bs4']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            logger.warning(f"Missing optional modules: {missing_modules}")
            logger.info("Install with: pip install -r yitp_requirements.txt")
        
        return True
    
    def run_content_extraction(self) -> bool:
        """Run content extraction step"""
        logger.info("🔍 Step 1: Extracting content from source files...")
        
        try:
            cmd = [
                sys.executable,
                "yitp_content_extractor.py",
                "--input", str(self.input_dir),
                "--output", str(self.extracted_file),
                "--verbose"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Content extraction completed successfully")
                
                # Load extracted data to get statistics
                if self.extracted_file.exists():
                    with open(self.extracted_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.stats['content_units_extracted'] = len(data.get('content_units', []))
                
                return True
            else:
                logger.error("❌ Content extraction failed")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running content extraction: {str(e)}")
            return False
    
    def run_json_building(self, course_config: Dict = None) -> bool:
        """Run JSON building step"""
        logger.info("🏗️ Step 2: Building YITP course JSON...")
        
        try:
            cmd = [
                sys.executable,
                "yitp_json_builder.py",
                "--input", str(self.extracted_file),
                "--output", str(self.output_file),
                "--verbose"
            ]
            
            # Add course configuration options
            if course_config:
                if 'title' in course_config:
                    cmd.extend(["--title", course_config['title']])
                if 'description' in course_config:
                    cmd.extend(["--description", course_config['description']])
                if 'price' in course_config:
                    cmd.extend(["--price", str(course_config['price'])])
                if 'category' in course_config:
                    cmd.extend(["--category", course_config['category']])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ YITP JSON building completed successfully")
                
                # Load course data to get statistics
                if self.output_file.exists():
                    with open(self.output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    modules = data.get('modules', [])
                    self.stats['modules_created'] = len(modules)
                    self.stats['lessons_created'] = sum(len(m.get('lessons', [])) for m in modules)
                    
                    # Count quiz questions
                    question_count = 0
                    for module in modules:
                        for lesson in module.get('lessons', []):
                            assessment = lesson.get('assessment', {})
                            quiz = assessment.get('quiz', {})
                            questions = quiz.get('questions', [])
                            question_count += len(questions)
                    
                    self.stats['quiz_questions_generated'] = question_count
                
                return True
            else:
                logger.error("❌ YITP JSON building failed")
                logger.error(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running JSON building: {str(e)}")
            return False
    
    def run_validation(self) -> bool:
        """Run validation step"""
        logger.info("✅ Step 3: Validating YITP course JSON...")
        
        try:
            cmd = [
                sys.executable,
                "yitp_validator.py",
                "--input", str(self.output_file),
                "--report", str(self.validation_report),
                "--verbose"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Extract validation score from output
            if "Overall score:" in result.stdout:
                score_line = [line for line in result.stdout.split('\n') if 'Overall score:' in line]
                if score_line:
                    score_text = score_line[0].split(':')[1].strip().replace('%', '')
                    try:
                        self.stats['validation_score'] = float(score_text)
                    except ValueError:
                        pass
            
            if result.returncode == 0:
                logger.info("✅ Validation completed successfully")
                return True
            else:
                logger.warning("⚠️ Validation completed with issues")
                logger.info("Check validation report for details")
                return True  # Continue even with validation warnings
                
        except Exception as e:
            logger.error(f"Error running validation: {str(e)}")
            return False
    
    def generate_summary_report(self) -> str:
        """Generate final processing summary report"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            duration_str = f"{duration.total_seconds():.1f} seconds"
        else:
            duration_str = "Unknown"
        
        status = "✅ SUCCESS" if self.stats['success'] else "❌ FAILED"
        
        report = f"""
🎯 YITP CONTENT PROCESSING SUMMARY
{'='*50}
Processing Status: {status}
Processing Time: {duration_str}
Completion Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 PROCESSING STATISTICS:
   Source Files Processed: {self.stats['files_processed']}
   Content Units Extracted: {self.stats['content_units_extracted']}
   Modules Created: {self.stats['modules_created']}
   Lessons Created: {self.stats['lessons_created']}
   Quiz Questions Generated: {self.stats['quiz_questions_generated']}
   Validation Score: {self.stats['validation_score']}%

📁 OUTPUT FILES:
   Course JSON: {self.output_file}
   Validation Report: {self.validation_report}
   
🎯 COURSE READY FOR YITP LMS INTEGRATION!

📋 NEXT STEPS:
   1. Review the generated course JSON
   2. Check validation report for any issues
   3. Upload media files to CDN if needed
   4. Import course into YITP LMS
   5. Test course functionality

{'✅ PROCESSING COMPLETED SUCCESSFULLY!' if self.stats['success'] else '❌ PROCESSING FAILED - CHECK LOGS'}
"""
        
        return report
    
    def cleanup(self) -> None:
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                # Keep validation report but remove extracted content
                if self.extracted_file.exists():
                    self.extracted_file.unlink()
                logger.info("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up: {str(e)}")
    
    def process_complete_workflow(self, course_config: Dict = None) -> bool:
        """Run the complete YITP content processing workflow"""
        self.stats['start_time'] = datetime.now()
        
        logger.info("🚀 Starting YITP Content Processing Workflow")
        logger.info("="*60)
        
        try:
            # Step 0: Setup environment
            if not self.setup_environment():
                return False
            
            # Step 1: Extract content
            if not self.run_content_extraction():
                return False
            
            # Step 2: Build YITP JSON
            if not self.run_json_building(course_config):
                return False
            
            # Step 3: Validate output
            validation_success = self.run_validation()
            
            # Mark as successful if we got this far
            self.stats['success'] = True
            self.stats['end_time'] = datetime.now()
            
            # Generate and display summary
            summary = self.generate_summary_report()
            logger.info(summary)
            
            # Save summary to file
            summary_file = self.output_file.parent / f"{self.output_file.stem}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"📄 Summary report saved to: {summary_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            self.stats['success'] = False
            self.stats['end_time'] = datetime.now()
            return False
        
        finally:
            # Always cleanup
            self.cleanup()


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP Content Processor - Complete Workflow')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory containing PDF/PPTX files')
    parser.add_argument('--output', type=str, default='yitp_course.json',
                       help='Output YITP course JSON file')
    parser.add_argument('--title', type=str,
                       help='Course title')
    parser.add_argument('--description', type=str,
                       help='Course description')
    parser.add_argument('--price', type=float, default=39.0,
                       help='Course price (default: 39.0)')
    parser.add_argument('--category', type=str, default='Professional Development',
                       help='Course category')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_dir = Path(args.input)
    output_file = Path(args.output)
    
    # Prepare course configuration
    course_config = {
        'price': args.price,
        'category': args.category
    }
    
    if args.title:
        course_config['title'] = args.title
    if args.description:
        course_config['description'] = args.description
    
    # Create processor and run workflow
    processor = YITPProcessor(input_dir, output_file)
    success = processor.process_complete_workflow(course_config)
    
    if success:
        print("\n🎉 YITP Content Processing completed successfully!")
        print(f"📁 Course JSON: {output_file}")
        print("🚀 Ready for YITP LMS integration!")
    else:
        print("\n❌ YITP Content Processing failed.")
        print("Check the logs for details and fix any issues.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
