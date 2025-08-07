"""
Simple test runner for the Candidate Recommendation Engine
Run this script to test all functionality.
"""

import os
import sys
import subprocess

def run_test():
    """Run the comprehensive test suite."""
    print("🚀 Starting Candidate Recommendation Engine Test Suite")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("engine"):
        print("❌ Error: Please run this script from the project root directory")
        return False
    
    # Check if test_engine.py exists
    if not os.path.exists("test_engine.py"):
        print("❌ Error: test_engine.py not found")
        return False
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, "test_engine.py"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        # Return success based on exit code
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_quick_test():
    """Run a quick test to check basic functionality."""
    print("🔍 Running quick functionality check...")
    
    try:
        # Test imports
        from engine.parser import clean_text, extract_candidate_info
        from engine.recommender import generate_content_hash, detect_duplicates
        
        print("✅ Basic imports successful")
        
        # Test text cleaning
        test_text = "  Hello   World  "
        cleaned = clean_text(test_text)
        assert "Hello World" in cleaned, "Text cleaning failed"
        print("✅ Text cleaning working")
        
        # Test content hash
        hash1 = generate_content_hash("test")
        hash2 = generate_content_hash("test")
        assert hash1 == hash2, "Content hash not consistent"
        print("✅ Content hash working")
        
        # Test duplicate detection
        candidates = [
            {"id": "1", "name": "John", "email": "john@test.com", "text": "test"},
            {"id": "2", "name": "Jane", "email": "john@test.com", "text": "test2"}
        ]
        unique, duplicates = detect_duplicates(candidates)
        assert len(unique) == 1, "Duplicate detection failed"
        print("✅ Duplicate detection working")
        
        print("🎉 Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    """Main function."""
    print("Choose test type:")
    print("1. Quick test (fast, basic functionality)")
    print("2. Full test (comprehensive, all features)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        success = run_quick_test()
    elif choice == "2":
        success = run_test()
    elif choice == "3":
        print("Goodbye!")
        return
    else:
        print("Invalid choice. Running quick test...")
        success = run_quick_test()
    
    if success:
        print("\n🎉 All tests passed! Your Candidate Recommendation Engine is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print("\nTo run the full application, use:")
    print("streamlit run app.py")

if __name__ == "__main__":
    main()
