#!/usr/bin/env python3
"""
Comprehensive test script for the Candidate Recommendation Engine
Tests all functionality including duplicate detection, file processing, similarity scoring, and summary generation.
"""

import os
import sys
import tempfile
import logging
from unittest.mock import Mock, patch
import pandas as pd

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    try:
        from engine.parser import extract_text_from_pdf, extract_text_from_docx, clean_text, extract_candidate_info
        from engine.similarity import generate_embeddings, calculate_similarity
        from engine.summarizer import generate_summary
        from engine.recommender import process_candidates, detect_duplicates, generate_content_hash
        from ml_utils.embedding_model import load_embedding_model
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_content_hash():
    """Test content hash generation."""
    print("\n🔍 Testing content hash generation...")
    try:
        from engine.recommender import generate_content_hash
        
        # Test normal text
        text1 = "Hello World"
        hash1 = generate_content_hash(text1)
        assert isinstance(hash1, str) and len(hash1) == 64, "Hash should be 64 characters"
        
        # Test empty text
        hash2 = generate_content_hash("")
        assert isinstance(hash2, str) and len(hash2) == 64, "Empty text should generate hash"
        
        # Test None text
        hash3 = generate_content_hash(None)
        assert isinstance(hash3, str) and len(hash3) == 64, "None text should generate hash"
        
        # Test same text produces same hash
        hash4 = generate_content_hash(text1)
        assert hash1 == hash4, "Same text should produce same hash"
        
        print("✅ Content hash generation working correctly")
        return True
    except Exception as e:
        print(f"❌ Content hash test failed: {e}")
        return False

def test_duplicate_detection():
    """Test duplicate detection functionality."""
    print("\n🔍 Testing duplicate detection...")
    try:
        from engine.recommender import detect_duplicates
        
        # Test data with duplicates
        candidates = [
            {
                "id": "File_1",
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "text": "Software Engineer with 5 years experience",
                "source": "file"
            },
            {
                "id": "File_2", 
                "name": "Jane Smith",
                "email": "john@example.com",  # Duplicate email
                "phone": "987-654-3210",
                "text": "Data Scientist with 3 years experience",
                "source": "file"
            },
            {
                "id": "Text_1",
                "name": "John Doe",
                "email": "john@example.com",  # Duplicate email
                "phone": "123-456-7890",
                "text": "Software Engineer with 5 years experience",  # Duplicate content
                "source": "manual"
            },
            {
                "id": "File_3",
                "name": "Bob Wilson",
                "email": "bob@example.com",
                "phone": "555-123-4567",
                "text": "Product Manager with 7 years experience",
                "source": "file"
            }
        ]
        
        unique_candidates, duplicate_info = detect_duplicates(candidates)
        
        # Should have 2 unique candidates (John Doe and Bob Wilson)
        assert len(unique_candidates) == 2, f"Expected 2 unique candidates, got {len(unique_candidates)}"
        
        # Should have 2 duplicates
        assert len(duplicate_info) == 2, f"Expected 2 duplicates, got {len(duplicate_info)}"
        
        # Check that John Doe (first occurrence) is kept
        kept_emails = [c["email"] for c in unique_candidates]
        assert "john@example.com" in kept_emails, "John Doe should be kept"
        assert "bob@example.com" in kept_emails, "Bob Wilson should be kept"
        
        print("✅ Duplicate detection working correctly")
        print(f"   - Found {len(duplicate_info)} duplicates")
        print(f"   - Kept {len(unique_candidates)} unique candidates")
        return True
    except Exception as e:
        print(f"❌ Duplicate detection test failed: {e}")
        return False

def test_text_processing():
    """Test text processing and cleaning."""
    print("\n🔍 Testing text processing...")
    try:
        from engine.parser import clean_text, extract_candidate_info
        
        # Test text cleaning
        dirty_text = "  Hello   World  \n\n  Test  "
        cleaned = clean_text(dirty_text)
        assert cleaned == "Hello World Test", f"Expected 'Hello World Test', got '{cleaned}'"
        
        # Test candidate info extraction
        resume_text = """
        John Doe
        Software Engineer
        john.doe@example.com
        (123) 456-7890
        
        Experience:
        - 5 years in software development
        - Python, JavaScript, React
        """
        
        info = extract_candidate_info(resume_text)
        assert info["name"] == "John Doe", f"Expected 'John Doe', got '{info['name']}'"
        assert "john.doe@example.com" in info["email"], f"Expected email, got '{info['email']}'"
        assert "123" in info["phone"], f"Expected phone, got '{info['phone']}'"
        
        print("✅ Text processing working correctly")
        return True
    except Exception as e:
        print(f"❌ Text processing test failed: {e}")
        return False

def test_similarity_calculation():
    """Test similarity calculation."""
    print("\n🔍 Testing similarity calculation...")
    try:
        from engine.similarity import generate_embeddings, calculate_similarity
        
        # Mock the embedding model
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        
        # Test embeddings generation
        texts = ["Software Engineer", "Data Scientist", "Product Manager"]
        embeddings = generate_embeddings(mock_model, texts)
        assert len(embeddings) == 3, f"Expected 3 embeddings, got {len(embeddings)}"
        
        # Test similarity calculation
        job_embedding = [0.1, 0.2, 0.3]
        candidate_embeddings = [[0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        similarities = calculate_similarity(job_embedding, candidate_embeddings)
        assert len(similarities) == 2, f"Expected 2 similarities, got {len(similarities)}"
        assert all(0 <= s <= 1 for s in similarities), "Similarities should be between 0 and 1"
        
        print("✅ Similarity calculation working correctly")
        return True
    except Exception as e:
        print(f"❌ Similarity calculation test failed: {e}")
        return False

def test_full_pipeline():
    """Test the full recommendation pipeline."""
    print("\n🔍 Testing full recommendation pipeline...")
    try:
        from engine.recommender import process_candidates
        
        # Mock the embedding model
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        
        # Mock the summarizer
        with patch('engine.recommender.generate_summary') as mock_summary:
            mock_summary.return_value = "This candidate shows good potential for the role."
            
            # Test data
            job_description = "We are looking for a Software Engineer with Python experience."
            uploaded_files = []  # No files for this test
            manual_texts = [
                """
                John Doe
                Software Engineer
                john.doe@example.com
                (123) 456-7890
                
                Experience:
                - 5 years in Python development
                - React, JavaScript, Node.js
                """,
                """
                Jane Smith
                Data Scientist
                jane.smith@example.com
                (987) 654-3210
                
                Experience:
                - 3 years in data science
                - Python, R, SQL
                """
            ]
            
            # Process candidates
            df, duplicate_info = process_candidates(mock_model, job_description, uploaded_files, manual_texts)
            
            # Check results
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) == 2, f"Expected 2 candidates, got {len(df)}"
            assert "Name" in df.columns, "DataFrame should have Name column"
            assert "Email" in df.columns, "DataFrame should have Email column"
            assert "Similarity Score" in df.columns, "DataFrame should have Similarity Score column"
            assert "AI Summary" in df.columns, "DataFrame should have AI Summary column"
            
            print("✅ Full pipeline working correctly")
            print(f"   - Processed {len(df)} candidates")
            print(f"   - Found {len(duplicate_info)} duplicates")
            return True
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and edge cases."""
    print("\n🔍 Testing error handling...")
    try:
        from engine.recommender import detect_duplicates, generate_content_hash
        
        # Test with empty candidates list
        unique_candidates, duplicate_info = detect_duplicates([])
        assert len(unique_candidates) == 0, "Empty list should return empty unique candidates"
        assert len(duplicate_info) == 0, "Empty list should return empty duplicate info"
        
        # Test with invalid candidate structure
        invalid_candidates = [{"name": "John"}, {"email": "test@example.com"}]  # Missing required fields
        unique_candidates, duplicate_info = detect_duplicates(invalid_candidates)
        # Should handle gracefully without crashing
        
        # Test content hash with various inputs
        assert generate_content_hash("") is not None, "Empty string should generate hash"
        assert generate_content_hash(None) is not None, "None should generate hash"
        
        print("✅ Error handling working correctly")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting comprehensive test of Candidate Recommendation Engine\n")
    
    tests = [
        ("Imports", test_imports),
        ("Content Hash", test_content_hash),
        ("Duplicate Detection", test_duplicate_detection),
        ("Text Processing", test_text_processing),
        ("Similarity Calculation", test_similarity_calculation),
        ("Full Pipeline", test_full_pipeline),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The engine is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
