"""
Adobe Hackathon 2025: Round 1B - Persona-Driven Document Intelligence
Analyzes documents based on persona and job-to-be-done requirements
"""

import fitz  # PyMuPDF
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class PersonaDrivenAnalyzer:
    def __init__(self):
        # Use a lightweight sentence transformer model (under 1GB requirement)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # ~90MB model
        self.tfidf = TfidfVectorizer(max_features=5000, stop_words='english')

    def analyze_documents(self, pdf_paths: List[str], persona: str, job_to_be_done: str) -> Dict:
        """Main function to analyze documents based on persona and job requirements"""
        start_time = time.time()

        try:
            # Extract content from all PDFs
            documents_content = []
            for pdf_path in pdf_paths:
                content = self._extract_pdf_content(pdf_path)
                documents_content.append(content)

            # Analyze persona and job requirements
            persona_embedding = self.model.encode([persona])
            job_embedding = self.model.encode([job_to_be_done])

            # Extract and rank sections
            relevant_sections = self._extract_relevant_sections(
                documents_content, persona_embedding, job_embedding, persona, job_to_be_done
            )

            # Extract sub-sections
            sub_sections = self._extract_subsections(
                documents_content, relevant_sections, persona_embedding, job_embedding
            )

            processing_time = time.time() - start_time

            # Structure output according to required format
            result = {
                "metadata": {
                    "input_documents": [os.path.basename(path) for path in pdf_paths],
                    "persona": persona,
                    "job_to_be_done": job_to_be_done,
                    "processing_timestamp": datetime.now().isoformat(),
                    "processing_time": processing_time,
                    "total_documents": len(pdf_paths)
                },
                "extracted_sections": relevant_sections,
                "sub_section_analysis": sub_sections
            }

            print(f"Analysis completed in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            print(f"Error analyzing documents: {str(e)}")
            return {"error": str(e)}

    def _extract_pdf_content(self, pdf_path: str) -> Dict:
        """Extract structured content from PDF"""
        doc = fitz.open(pdf_path)
        content = {
            "filename": os.path.basename(pdf_path),
            "pages": [],
            "total_pages": len(doc)
        }

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract text with structure information
            blocks = page.get_text("dict")["blocks"]
            page_content = {
                "page_number": page_num + 1,
                "sections": [],
                "full_text": page.get_text()
            }

            # Group text into potential sections
            current_section = {"title": "", "content": "", "font_info": []}

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        max_font_size = 0

                        for span in line["spans"]:
                            line_text += span["text"]
                            max_font_size = max(max_font_size, span["size"])

                        line_text = line_text.strip()
                        if line_text:
                            # Potential section header (larger font or formatting)
                            if (max_font_size > 12 and len(line_text) < 100 and 
                                not line_text.endswith('.') and len(line_text) > 5):

                                # Save previous section if it has content
                                if current_section["content"].strip():
                                    page_content["sections"].append(current_section.copy())

                                # Start new section
                                current_section = {
                                    "title": line_text,
                                    "content": "",
                                    "font_size": max_font_size
                                }
                            else:
                                current_section["content"] += " " + line_text

            # Add final section
            if current_section["content"].strip():
                page_content["sections"].append(current_section)

            content["pages"].append(page_content)

        doc.close()
        return content

    def _extract_relevant_sections(self, documents_content: List[Dict], 
                                 persona_embedding: np.ndarray, 
                                 job_embedding: np.ndarray,
                                 persona: str, job_to_be_done: str) -> List[Dict]:
        """Extract and rank sections based on relevance to persona and job"""

        all_sections = []

        # Collect all sections from all documents
        for doc_content in documents_content:
            for page in doc_content["pages"]:
                for section in page["sections"]:
                    if len(section["content"].strip()) > 50:  # Minimum content length
                        all_sections.append({
                            "document": doc_content["filename"],
                            "page_number": page["page_number"],
                            "section_title": section["title"] or "Untitled Section",
                            "content": section["content"].strip(),
                            "font_size": section.get("font_size", 12)
                        })

        # Calculate relevance scores
        section_texts = [s["content"] for s in all_sections]
        if not section_texts:
            return []

        # Get embeddings for all sections
        section_embeddings = self.model.encode(section_texts)

        # Calculate similarity scores
        persona_similarities = cosine_similarity(section_embeddings, persona_embedding).flatten()
        job_similarities = cosine_similarity(section_embeddings, job_embedding).flatten()

        # Keyword-based scoring for additional relevance
        keyword_scores = self._calculate_keyword_scores(section_texts, persona, job_to_be_done)

        # Combine scores (weighted)
        combined_scores = (0.4 * persona_similarities + 
                          0.4 * job_similarities + 
                          0.2 * keyword_scores)

        # Rank sections
        scored_sections = []
        for i, section in enumerate(all_sections):
            section["relevance_score"] = float(combined_scores[i])
            section["importance_rank"] = 0  # Will be set after sorting
            scored_sections.append(section)

        # Sort by relevance score
        scored_sections.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Assign importance ranks and return top sections
        top_sections = scored_sections[:15]  # Top 15 most relevant sections
        for i, section in enumerate(top_sections):
            section["importance_rank"] = i + 1
            # Remove relevance_score from final output (internal use only)
            del section["relevance_score"]

        return top_sections

    def _extract_subsections(self, documents_content: List[Dict], 
                           relevant_sections: List[Dict],
                           persona_embedding: np.ndarray,
                           job_embedding: np.ndarray) -> List[Dict]:
        """Extract granular sub-sections from relevant sections"""

        sub_sections = []

        for section in relevant_sections[:10]:  # Top 10 sections for sub-analysis
            # Split section content into sentences/paragraphs
            sentences = sent_tokenize(section["content"])

            # Group sentences into sub-sections (every 2-3 sentences)
            current_subsection = ""
            subsection_count = 0

            for i, sentence in enumerate(sentences):
                current_subsection += sentence + " "

                # Create sub-section every 2-3 sentences or at natural breaks
                if ((i + 1) % 3 == 0 or i == len(sentences) - 1) and len(current_subsection.strip()) > 100:
                    subsection_count += 1

                    # Calculate relevance for this sub-section
                    subsection_embedding = self.model.encode([current_subsection])
                    persona_sim = cosine_similarity(subsection_embedding, persona_embedding)[0][0]
                    job_sim = cosine_similarity(subsection_embedding, job_embedding)[0][0]

                    relevance_score = 0.5 * persona_sim + 0.5 * job_sim

                    # Only include highly relevant sub-sections
                    if relevance_score > 0.3:
                        sub_sections.append({
                            "document": section["document"],
                            "page_number": section["page_number"],
                            "parent_section": section["section_title"],
                            "subsection_id": f"{section['document']}_p{section['page_number']}_s{subsection_count}",
                            "refined_text": current_subsection.strip(),
                            "relevance_score": float(relevance_score)
                        })

                    current_subsection = ""

        # Sort sub-sections by relevance and return top ones
        sub_sections.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Remove relevance_score and return top 20 sub-sections
        final_subsections = sub_sections[:20]
        for subsection in final_subsections:
            del subsection["relevance_score"]

        return final_subsections

    def _calculate_keyword_scores(self, texts: List[str], persona: str, job_to_be_done: str) -> np.ndarray:
        """Calculate keyword-based relevance scores"""

        # Extract keywords from persona and job description
        persona_keywords = self._extract_keywords(persona.lower())
        job_keywords = self._extract_keywords(job_to_be_done.lower())
        all_keywords = persona_keywords + job_keywords

        scores = []
        for text in texts:
            text_lower = text.lower()

            # Count keyword matches
            keyword_matches = sum(1 for keyword in all_keywords if keyword in text_lower)

            # Normalize by text length
            score = keyword_matches / max(len(text.split()), 1)
            scores.append(score)

        # Normalize scores to 0-1 range
        if scores:
            max_score = max(scores)
            if max_score > 0:
                scores = [s / max_score for s in scores]

        return np.array(scores)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = re.findall(r'\b\w{3,}\b', text)

        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'her', 'was', 'one', 'our', 'had', 'has', 'what', 'who', 'when', 'where', 'why', 'how', 'that', 'this', 'with', 'from', 'they', 'she', 'him', 'his', 'her', 'its', 'our', 'their'}

        keywords = [word for word in words if word.lower() not in stop_words and len(word) > 3]
        return keywords[:10]  # Return top 10 keywords

def main():
    """Main function for Docker execution"""
    input_dir = "/app/input"
    output_dir = "/app/output"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    analyzer = PersonaDrivenAnalyzer()

    # Read configuration file for persona and job-to-be-done
    config_path = os.path.join(input_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        persona = config.get("persona", "General Researcher")
        job_to_be_done = config.get("job_to_be_done", "Analyze the provided documents")
    else:
        # Default values if no config provided
        persona = "General Researcher"
        job_to_be_done = "Analyze and extract key insights from the provided documents"

    # Collect all PDF files
    pdf_files = []
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(input_dir, filename))

    if pdf_files:
        print(f"Processing {len(pdf_files)} documents with persona: {persona}")
        print(f"Job to be done: {job_to_be_done}")

        # Analyze documents
        result = analyzer.analyze_documents(pdf_files, persona, job_to_be_done)

        # Save result
        output_path = os.path.join(output_dir, "analysis_result.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"Analysis completed and saved to analysis_result.json")
    else:
        print("No PDF files found in input directory")

if __name__ == "__main__":
    main()
