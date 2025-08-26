"""Demo script for the Lawyer Agent compliance system"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.compliance_engine import ComplianceEngine
from utils.test_processor import TestDatasetProcessor
from loguru import logger

def run_demo():
    """Run demonstration of the lawyer agent system"""
    
    print("=" * 60)
    print("LAWYER AGENT - COMPLIANCE DETECTION SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize system
    print("\n1. Initializing Compliance Engine...")
    try:
        engine = ComplianceEngine()
        print("✅ System initialized successfully!")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Demo test cases
    test_cases = [
        {
            "title": "EU Location-based Content Blocking",
            "text": """
            Title: Location-based Content Blocking
            Description: Feature reads user location to enforce France's copyright rules (download blocking)
            Geographic Scope: EU, France
            User Stories:
            - As a user in France, I cannot download certain copyrighted content
            - As a content creator, my content is geo-blocked in specific regions
            Technical Requirements:
            - Location detection API integration
            - Copyright rule engine
            - Download blocking mechanism
            Data Processing: user location tracking, geolocation services
            """
        },
        {
            "title": "Age Gate for Minors",
            "text": """
            Title: Age Verification System
            Description: Requires age gates specific to minor protection laws
            Target Users: children under 18, minors
            User Stories:
            - As a parent, I want to control my child's access to the platform
            - As a minor user, I am prompted for age verification
            Technical Requirements:
            - Age verification API
            - Parental consent workflow
            - Account restriction logic
            Geographic Scope: California, Utah, Florida
            """
        },
        {
            "title": "Business Market Testing",
            "text": """
            Title: US Market Feature Rollout
            Description: Geofences feature rollout in US for market testing
            Geographic Scope: United States
            User Stories:
            - As a product manager, I want to test new features in specific markets
            - As a US user, I get access to beta features
            Technical Requirements:
            - Geographic feature flags
            - A/B testing infrastructure
            - Market segmentation logic
            Note: Business-driven deployment, not legal requirement
            """
        }
    ]
    
    print(f"\n2. Analyzing {len(test_cases)} Test Cases...")
    print("-" * 40)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {case['title']}")
        print("-" * 30)
        
        try:
            # Perform compliance assessment
            assessment = engine.assess_feature_compliance(case['text'])
            
            # Display results
            print(f"Requires Compliance: {'✅ YES' if assessment.requires_compliance else '❌ NO'}")
            print(f"Confidence Score: {assessment.confidence:.2f}")
            print(f"Reasoning: {assessment.reasoning}")
            
            if assessment.matched_regulations:
                print(f"\nMatched Regulations ({len(assessment.matched_regulations)}):")
                for match in assessment.matched_regulations[:3]:  # Show top 3
                    print(f"  • {match.regulation_name}")
                    print(f"    Similarity: {match.similarity_score:.2f}")
                    print(f"    Confidence: {match.confidence_score:.2f}")
            
            if assessment.compliance_indicators:
                print(f"\nCompliance Indicators ({len(assessment.compliance_indicators)}):")
                for indicator in assessment.compliance_indicators:
                    print(f"  • {indicator.category}: {indicator.text}")
            
        except Exception as e:
            print(f"❌ Error analyzing case: {e}")
        
        print("-" * 30)
    
    # Demo batch processing
    print(f"\n3. Demonstrating Batch Processing...")
    try:
        processor = TestDatasetProcessor()
        
        # Create sample test cases
        sample_path = processor.create_sample_test_cases()
        print(f"✅ Created sample test cases: {sample_path}")
        
        # Process them
        output_path = processor.process_json_dataset(sample_path)
        print(f"✅ Generated CSV results: {output_path}")
        
        # Show a few results
        import pandas as pd
        df = pd.read_csv(output_path)
        print(f"\n📊 Batch Results Summary:")
        print(f"Total cases processed: {len(df)}")
        print(f"Require compliance: {df['requires_compliance'].sum()}")
        print(f"Average confidence: {df['confidence'].mean():.2f}")
        
    except Exception as e:
        print(f"❌ Batch processing demo failed: {e}")
    
    # System statistics
    print(f"\n4. System Statistics...")
    try:
        stats = engine.vector_store.get_stats()
        print(f"✅ Vector Database Status: {stats['status']}")
        print(f"✅ Total Documents Indexed: {stats.get('total_documents', 0)}")
        print(f"✅ Regulations Covered: {stats.get('regulations_count', 0)}")
        print(f"✅ Embedding Dimension: {stats.get('embedding_dimension', 0)}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    
    print(f"\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nTo run the API server:")
    print("cd src/api && python main.py")
    print("\nAPI will be available at: http://localhost:5000")
    print("\nEndpoints:")
    print("- POST /analyze - Single feature analysis")
    print("- POST /batch-analyze - Multiple feature analysis")
    print("- GET /system-status - System health check")
    print("=" * 60)

if __name__ == "__main__":
    # Configure logging
    logger.add(sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")
    
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()