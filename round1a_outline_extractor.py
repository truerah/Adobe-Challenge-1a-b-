"""
Adobe Hackathon 2025: Round 1A - PDF Outline Extractor
Extracts structured outlines from PDFs with title and hierarchical headings (H1, H2, H3)
"""

import fitz  # PyMuPDF
import json
import re
import os
from collections import Counter
from typing import Dict, List, Tuple, Optional
import time

class PDFOutlineExtractor:
    def __init__(self):
        self.font_size_threshold = 2.0  # Minimum difference for heading detection
        self.common_headings = [
            'introduction', 'conclusion', 'abstract', 'summary', 'overview',
            'methodology', 'results', 'discussion', 'references', 'appendix',
            'background', 'literature review', 'analysis', 'findings'
        ]

    def extract_outline(self, pdf_path: str) -> Dict:
        """Main function to extract outline from PDF"""
        start_time = time.time()

        try:
            doc = fitz.open(pdf_path)

            # Extract title from first page
            title = self._extract_title(doc)

            # Extract headings with multi-strategy approach
            headings = self._extract_headings(doc)

            # Structure the outline
            outline = self._structure_outline(headings)

            doc.close()

            processing_time = time.time() - start_time
            print(f"Processing completed in {processing_time:.2f} seconds")

            return {
                "title": title,
                "outline": outline,
                "metadata": {
                    "processing_time": processing_time,
                    "total_pages": len(doc),
                    "headings_found": len(outline)
                }
            }

        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return {"title": "", "outline": [], "error": str(e)}

    def _extract_title(self, doc) -> str:
        """Extract document title from first page using multiple strategies"""
        first_page = doc[0]

        # Strategy 1: Look for largest font size text
        blocks = first_page.get_text("dict")["blocks"]
        font_sizes = []
        texts_with_fonts = []

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_size = span["size"]
                        text = span["text"].strip()
                        if text and len(text) > 3:  # Ignore very short text
                            font_sizes.append(font_size)
                            texts_with_fonts.append((text, font_size, span["bbox"][1]))  # Include y-position

        if texts_with_fonts:
            # Find texts with largest font size in top portion of page
            max_font_size = max(font_sizes)
            title_candidates = [
                text for text, size, y_pos in texts_with_fonts 
                if size >= max_font_size - 1 and y_pos < 200  # Top portion of page
            ]

            if title_candidates:
                # Choose the longest reasonable title
                title = max(title_candidates, key=len)
                # Clean up title
                title = re.sub(r'\s+', ' ', title).strip()
                if len(title) > 100:  # Too long, try shorter one
                    shorter_candidates = [t for t in title_candidates if len(t) <= 100]
                    if shorter_candidates:
                        title = shorter_candidates[0]
                return title

        # Fallback: Use PDF metadata or filename
        metadata_title = doc.metadata.get("title", "").strip()
        if metadata_title:
            return metadata_title

        return "Untitled Document"

    def _extract_headings(self, doc) -> List[Tuple]:
        """Extract headings using multi-strategy approach"""
        all_headings = []

        # Get font analysis for the entire document
        font_stats = self._analyze_fonts(doc)
        body_font_size = font_stats["body_font_size"]
        heading_font_sizes = font_stats["heading_font_sizes"]

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Strategy 1: Font-based detection
            font_headings = self._extract_by_font(page, page_num, body_font_size, heading_font_sizes)

            # Strategy 2: Pattern-based detection
            pattern_headings = self._extract_by_patterns(page, page_num)

            # Strategy 3: Position-based detection
            position_headings = self._extract_by_position(page, page_num)

            # Combine and deduplicate
            page_headings = self._combine_strategies(font_headings, pattern_headings, position_headings)
            all_headings.extend(page_headings)

        return all_headings

    def _analyze_fonts(self, doc) -> Dict:
        """Analyze font usage across the document to identify patterns"""
        font_sizes = []
        font_usage = Counter()

        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            size = round(span["size"], 1)
                            font_sizes.append(size)
                            font_usage[size] += len(span["text"])

        # Find most common font size (likely body text)
        if font_usage:
            body_font_size = font_usage.most_common(1)[0][0]

            # Identify potential heading font sizes (larger than body)
            heading_font_sizes = [size for size in font_usage.keys() 
                                if size > body_font_size + self.font_size_threshold]
            heading_font_sizes.sort(reverse=True)
        else:
            body_font_size = 12.0
            heading_font_sizes = [16.0, 14.0]

        return {
            "body_font_size": body_font_size,
            "heading_font_sizes": heading_font_sizes,
            "font_distribution": dict(font_usage)
        }

    def _extract_by_font(self, page, page_num: int, body_font_size: float, heading_font_sizes: List[float]) -> List[Tuple]:
        """Extract headings based on font size analysis"""
        headings = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    line_font_size = 0

                    for span in line["spans"]:
                        line_text += span["text"]
                        line_font_size = max(line_font_size, span["size"])

                    line_text = line_text.strip()

                    # Check if this could be a heading
                    if (line_text and 
                        len(line_text) > 2 and 
                        len(line_text) < 200 and
                        line_font_size > body_font_size + self.font_size_threshold):

                        # Determine heading level based on font size
                        level = self._determine_heading_level(line_font_size, heading_font_sizes)

                        headings.append((level, line_text, page_num + 1, line_font_size, "font"))

        return headings

    def _extract_by_patterns(self, page, page_num: int) -> List[Tuple]:
        """Extract headings based on text patterns"""
        headings = []
        text = page.get_text()
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Pattern 1: Numbered sections (1., 1.1, 1.1.1, etc.)
            if re.match(r'^\d+(\.\d+)*\.?\s+', line):
                level = len(re.findall(r'\.', line.split()[0])) + 1
                level = min(level, 3)  # Cap at H3
                text = re.sub(r'^\d+(\.\d+)*\.?\s+', '', line)
                headings.append((f"H{level}", text, page_num + 1, 0, "pattern"))

            # Pattern 2: Common heading words
            elif any(keyword in line.lower() for keyword in self.common_headings):
                if len(line) < 100:  # Reasonable heading length
                    headings.append(("H2", line, page_num + 1, 0, "pattern"))

            # Pattern 3: All caps (potential headings)
            elif line.isupper() and len(line) < 80:
                headings.append(("H2", line.title(), page_num + 1, 0, "pattern"))

        return headings

    def _extract_by_position(self, page, page_num: int) -> List[Tuple]:
        """Extract headings based on position and formatting"""
        headings = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if len(line["spans"]) == 1:  # Single span (potentially standalone heading)
                        span = line["spans"][0]
                        text = span["text"].strip()

                        # Check for bold text (potential heading)
                        if (text and 
                            len(text) < 150 and 
                            span["flags"] & 2**4):  # Bold flag
                            headings.append(("H2", text, page_num + 1, span["size"], "position"))

        return headings

    def _determine_heading_level(self, font_size: float, heading_font_sizes: List[float]) -> str:
        """Determine heading level based on font size"""
        if not heading_font_sizes:
            return "H2"

        for i, size in enumerate(heading_font_sizes):
            if font_size >= size - 0.5:  # Small tolerance
                return f"H{min(i + 1, 3)}"

        return "H3"

    def _combine_strategies(self, font_headings: List, pattern_headings: List, position_headings: List) -> List:
        """Combine results from different strategies and remove duplicates"""
        all_headings = font_headings + pattern_headings + position_headings

        # Remove duplicates based on text similarity
        unique_headings = []
        seen_texts = set()

        for heading in all_headings:
            level, text, page, font_size, strategy = heading
            text_normalized = re.sub(r'\s+', ' ', text.lower().strip())

            if text_normalized not in seen_texts and len(text.strip()) > 2:
                seen_texts.add(text_normalized)
                unique_headings.append((level, text.strip(), page, font_size, strategy))

        # Sort by page number
        unique_headings.sort(key=lambda x: x[2])

        return unique_headings

    def _structure_outline(self, headings: List[Tuple]) -> List[Dict]:
        """Convert headings to the required JSON format"""
        outline = []

        for level, text, page, font_size, strategy in headings:
            outline.append({
                "level": level,
                "text": text,
                "page": page
            })

        return outline

def main():
    """Main function for Docker execution"""
    input_dir = "/app/input"
    output_dir = "/app/output"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    extractor = PDFOutlineExtractor()

    # Process all PDF files in input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            output_filename = filename.replace('.pdf', '.json')
            output_path = os.path.join(output_dir, output_filename)

            print(f"Processing {filename}...")

            # Extract outline
            result = extractor.extract_outline(pdf_path)

            # Save result
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"Saved outline to {output_filename}")

if __name__ == "__main__":
    main()
