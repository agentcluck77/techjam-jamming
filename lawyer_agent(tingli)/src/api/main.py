"""Flask API for the Lawyer Agent compliance system"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger
import json
from typing import Dict, Any
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.compliance_engine import ComplianceEngine
from core.feature_analyzer import FeatureAnalyzer
from database.vector_store import VectorStore

app = Flask(__name__)
CORS(app)

# Initialize the compliance system
compliance_engine = None
feature_analyzer = None

def initialize_system():
    """Initialize the compliance system"""
    global compliance_engine, feature_analyzer
    try:
        logger.info("Initializing lawyer agent system...")
        compliance_engine = ComplianceEngine()
        feature_analyzer = FeatureAnalyzer()
        logger.info("System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'lawyer-agent',
        'version': '1.0.0'
    })

@app.route('/analyze', methods=['POST'])
def analyze_feature():
    """Analyze a feature for compliance requirements"""
    try:
        if not compliance_engine:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json()
        if not data or 'feature_text' not in data:
            return jsonify({'error': 'Missing feature_text in request'}), 400
        
        feature_text = data['feature_text']
        logger.info(f"Analyzing feature compliance for: {feature_text[:100]}...")
        
        # Perform compliance assessment
        assessment = compliance_engine.assess_feature_compliance(feature_text)
        
        # Return assessment as JSON
        return jsonify({
            'status': 'success',
            'assessment': assessment.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing feature: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/batch-analyze', methods=['POST'])
def batch_analyze_features():
    """Analyze multiple features for compliance requirements"""
    try:
        if not compliance_engine:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json()
        if not data or 'features' not in data:
            return jsonify({'error': 'Missing features array in request'}), 400
        
        features = data['features']
        if not isinstance(features, list):
            return jsonify({'error': 'Features must be an array'}), 400
        
        logger.info(f"Batch analyzing {len(features)} features")
        
        results = []
        for i, feature_data in enumerate(features):
            try:
                if isinstance(feature_data, dict):
                    feature_text = feature_data.get('feature_text', '')
                    feature_id = feature_data.get('id', f'feature_{i}')
                else:
                    feature_text = str(feature_data)
                    feature_id = f'feature_{i}'
                
                if not feature_text:
                    results.append({
                        'id': feature_id,
                        'status': 'error',
                        'error': 'Empty feature text'
                    })
                    continue
                
                assessment = compliance_engine.assess_feature_compliance(feature_text)
                results.append({
                    'id': feature_id,
                    'status': 'success',
                    'assessment': assessment.to_dict()
                })
                
            except Exception as e:
                logger.error(f"Error analyzing feature {i}: {e}")
                results.append({
                    'id': feature_id if 'feature_id' in locals() else f'feature_{i}',
                    'status': 'error',
                    'error': str(e)
                })
        
        return jsonify({
            'status': 'success',
            'total_features': len(features),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/parse-feature', methods=['POST'])
def parse_feature_document():
    """Parse a raw feature document into structured format"""
    try:
        if not feature_analyzer:
            return jsonify({'error': 'System not initialized'}), 500
        
        data = request.get_json()
        if not data or 'document_text' not in data:
            return jsonify({'error': 'Missing document_text in request'}), 400
        
        document_text = data['document_text']
        feature_doc = feature_analyzer.parse_document(document_text)
        indicators = feature_analyzer.extract_compliance_indicators(feature_doc)
        
        return jsonify({
            'status': 'success',
            'parsed_document': {
                'title': feature_doc.title,
                'description': feature_doc.description,
                'user_stories': feature_doc.user_stories,
                'technical_requirements': feature_doc.technical_requirements,
                'geographic_scope': feature_doc.geographic_scope,
                'target_users': feature_doc.target_users,
                'data_processing': feature_doc.data_processing,
                'additional_context': feature_doc.additional_context
            },
            'compliance_indicators': [
                {
                    'text': ind.text,
                    'confidence': ind.confidence,
                    'category': ind.category,
                    'keywords': ind.keywords
                }
                for ind in indicators
            ]
        })
        
    except Exception as e:
        logger.error(f"Error parsing feature document: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/regulations', methods=['GET'])
def get_regulations():
    """Get information about available regulations"""
    try:
        from database.law_loader import LawLoader
        law_loader = LawLoader()
        regulations = law_loader.load_regulations()
        
        return jsonify({
            'status': 'success',
            'regulations': [
                {
                    'id': reg['id'],
                    'name': reg['name'],
                    'description': reg['description']
                }
                for reg in regulations
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting regulations: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/system-status', methods=['GET'])
def system_status():
    """Get system status and statistics"""
    try:
        status = {
            'compliance_engine': compliance_engine is not None,
            'feature_analyzer': feature_analyzer is not None
        }
        
        if compliance_engine:
            vector_stats = compliance_engine.vector_store.get_stats()
            status['vector_store'] = vector_stats
        
        return jsonify({
            'status': 'success',
            'system_status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Configure logging
    logger.add(sys.stdout, level="INFO")
    
    # Initialize system
    if not initialize_system():
        logger.error("Failed to initialize system, exiting")
        sys.exit(1)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)