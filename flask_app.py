"""
Adobe Hackathon 2025: Web Interface for PDF Analysis
Flask application providing interactive demo of Round 1A and Round 1B
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import tempfile
import shutil
from werkzeug.utils import secure_filename
import time
import uuid
from datetime import datetime
import zipfile
import io

# Import our analysis modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from round1a_outline_extractor import PDFOutlineExtractor
    from round1b_document_intelligence import PersonaDrivenAnalyzer
except ImportError:
    # For standalone demo, create mock classes
    class PDFOutlineExtractor:
        def extract_outline(self, pdf_path):
            return {
                "title": "Sample Document Analysis",
                "outline": [
                    {"level": "H1", "text": "Introduction", "page": 1},
                    {"level": "H2", "text": "Background", "page": 2},
                    {"level": "H3", "text": "Key Concepts", "page": 2},
                    {"level": "H2", "text": "Methodology", "page": 3},
                    {"level": "H3", "text": "Data Collection", "page": 4},
                    {"level": "H3", "text": "Analysis Framework", "page": 5},
                    {"level": "H2", "text": "Results", "page": 6},
                    {"level": "H2", "text": "Discussion", "page": 8},
                    {"level": "H2", "text": "Conclusion", "page": 10}
                ],
                "metadata": {
                    "processing_time": 2.3,
                    "total_pages": 12,
                    "headings_found": 9
                }
            }

    class PersonaDrivenAnalyzer:
        def analyze_documents(self, pdf_paths, persona, job_to_be_done):
            return {
                "metadata": {
                    "input_documents": [os.path.basename(p) for p in pdf_paths],
                    "persona": persona,
                    "job_to_be_done": job_to_be_done,
                    "processing_timestamp": datetime.now().isoformat(),
                    "processing_time": 15.7,
                    "total_documents": len(pdf_paths)
                },
                "extracted_sections": [
                    {
                        "document": "sample1.pdf",
                        "page_number": 1,
                        "section_title": "Executive Summary",
                        "importance_rank": 1
                    },
                    {
                        "document": "sample1.pdf", 
                        "page_number": 3,
                        "section_title": "Key Findings",
                        "importance_rank": 2
                    },
                    {
                        "document": "sample2.pdf",
                        "page_number": 2,
                        "section_title": "Methodology Overview",
                        "importance_rank": 3
                    }
                ],
                "sub_section_analysis": [
                    {
                        "document": "sample1.pdf",
                        "page_number": 1,
                        "refined_text": "This analysis demonstrates key insights relevant to the specified persona and objectives."
                    }
                ]
            }

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize analyzers
outline_extractor = PDFOutlineExtractor()
intelligence_analyzer = PersonaDrivenAnalyzer()

# Store session data (in production, use Redis or database)
sessions = {}

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Analysis dashboard"""
    return render_template('dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for Round 1A analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_dir, exist_ok=True)

        file_path = os.path.join(session_dir, filename)
        file.save(file_path)

        # Process with Round 1A extractor
        result = outline_extractor.extract_outline(file_path)

        # Store session data
        sessions[session_id] = {
            'files': [file_path],
            'round1a_result': result,
            'upload_time': datetime.now().isoformat()
        }

        return jsonify({
            'session_id': session_id,
            'filename': filename,
            'result': result,
            'success': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_multiple', methods=['POST'])
def upload_multiple_files():
    """Handle multiple file upload for Round 1B analysis"""
    try:
        files = request.files.getlist('files')
        persona = request.form.get('persona', 'General Researcher')
        job_to_be_done = request.form.get('job_to_be_done', 'Analyze documents')

        if not files or len(files) == 0:
            return jsonify({'error': 'No files provided'}), 400

        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed'}), 400

        # Create session directory
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Save all files
        file_paths = []
        for file in files:
            if file.filename and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(session_dir, filename)
                file.save(file_path)
                file_paths.append(file_path)

        if not file_paths:
            return jsonify({'error': 'No valid PDF files found'}), 400

        # Process with Round 1B analyzer
        result = intelligence_analyzer.analyze_documents(file_paths, persona, job_to_be_done)

        # Store session data
        sessions[session_id] = {
            'files': file_paths,
            'round1b_result': result,
            'persona': persona,
            'job_to_be_done': job_to_be_done,
            'upload_time': datetime.now().isoformat()
        }

        return jsonify({
            'session_id': session_id,
            'result': result,
            'success': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>')
def get_session(session_id):
    """Get session data"""
    if session_id in sessions:
        return jsonify(sessions[session_id])
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/api/download/<session_id>')
def download_results(session_id):
    """Download analysis results as JSON"""
    try:
        if session_id not in sessions:
            return jsonify({'error': 'Session not found'}), 404

        session_data = sessions[session_id]

        # Create downloadable JSON
        if 'round1a_result' in session_data:
            result = session_data['round1a_result']
            filename = 'outline_analysis.json'
        elif 'round1b_result' in session_data:
            result = session_data['round1b_result'] 
            filename = 'intelligence_analysis.json'
        else:
            return jsonify({'error': 'No results found'}), 404

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(result, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()

        return send_file(temp_file.name, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/demo/sample_outline')
def demo_sample_outline():
    """Provide sample outline data for demo"""
    sample_result = {
        "title": "Artificial Intelligence in Modern Healthcare",
        "outline": [
            {"level": "H1", "text": "Introduction to AI in Healthcare", "page": 1},
            {"level": "H2", "text": "Current Applications", "page": 2},
            {"level": "H3", "text": "Diagnostic Imaging", "page": 3},
            {"level": "H3", "text": "Drug Discovery", "page": 4},
            {"level": "H2", "text": "Machine Learning Techniques", "page": 5},
            {"level": "H3", "text": "Deep Learning Models", "page": 6},
            {"level": "H3", "text": "Natural Language Processing", "page": 7},
            {"level": "H2", "text": "Challenges and Limitations", "page": 8},
            {"level": "H3", "text": "Data Privacy Concerns", "page": 9},
            {"level": "H3", "text": "Regulatory Compliance", "page": 10},
            {"level": "H2", "text": "Future Directions", "page": 11},
            {"level": "H2", "text": "Conclusion", "page": 12}
        ],
        "metadata": {
            "processing_time": 3.2,
            "total_pages": 12,
            "headings_found": 12
        }
    }

    return jsonify({
        'session_id': 'demo_' + str(uuid.uuid4()),
        'filename': 'ai_healthcare_sample.pdf',
        'result': sample_result,
        'success': True,
        'demo': True
    })

@app.route('/api/demo/sample_intelligence')
def demo_sample_intelligence():
    """Provide sample intelligence analysis for demo"""
    sample_result = {
        "metadata": {
            "input_documents": ["research_paper_1.pdf", "research_paper_2.pdf", "research_paper_3.pdf"],
            "persona": "PhD Researcher in Machine Learning",
            "job_to_be_done": "Conduct literature review on neural networks for medical applications",
            "processing_timestamp": datetime.now().isoformat(),
            "processing_time": 45.3,
            "total_documents": 3
        },
        "extracted_sections": [
            {
                "document": "research_paper_1.pdf",
                "page_number": 2,
                "section_title": "Convolutional Neural Networks for Medical Imaging",
                "importance_rank": 1
            },
            {
                "document": "research_paper_2.pdf",
                "page_number": 1,
                "section_title": "Deep Learning in Diagnostic Applications",
                "importance_rank": 2
            },
            {
                "document": "research_paper_3.pdf",
                "page_number": 4,
                "section_title": "Performance Benchmarks and Evaluation Metrics",
                "importance_rank": 3
            },
            {
                "document": "research_paper_1.pdf",
                "page_number": 5,
                "section_title": "Transfer Learning for Medical Data",
                "importance_rank": 4
            },
            {
                "document": "research_paper_2.pdf",
                "page_number": 7,
                "section_title": "Clinical Validation and Results",
                "importance_rank": 5
            }
        ],
        "sub_section_analysis": [
            {
                "document": "research_paper_1.pdf",
                "page_number": 2,
                "refined_text": "Convolutional neural networks have shown remarkable success in medical image analysis, particularly in radiology and pathology applications. The hierarchical feature learning capability enables automatic detection of complex patterns in medical imaging data."
            },
            {
                "document": "research_paper_2.pdf", 
                "page_number": 1,
                "refined_text": "Deep learning models demonstrate superior performance compared to traditional machine learning approaches in diagnostic tasks. Key advantages include end-to-end learning and reduced need for manual feature engineering."
            },
            {
                "document": "research_paper_3.pdf",
                "page_number": 4,
                "refined_text": "Evaluation metrics for medical AI systems must consider both accuracy and clinical relevance. Sensitivity, specificity, and area under the ROC curve are standard measures, but clinical impact assessment is equally important."
            }
        ]
    }

    return jsonify({
        'session_id': 'demo_' + str(uuid.uuid4()),
        'result': sample_result,
        'success': True,
        'demo': True
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Adobe Hackathon Demo Server")
    print("📱 Features: Round 1A Outline Extraction + Round 1B Intelligence Analysis")
    print("🌐 Access: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
