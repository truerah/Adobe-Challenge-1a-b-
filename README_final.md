# 🚀 Connecting the Dots – Adobe Hackathon Project

An AI-powered full-stack web application built with **React + Flask + Python**, designed for Adobe’s *“Connecting the Dots”* hackathon. It extracts structured outlines from PDFs (Round 1A) and ranks document sections by persona relevance (Round 1B). The system runs fully offline using optimized CPU-only NLP models.

---

## 🧠 Key Features

### ✅ Round 1A – PDF Outline Extraction
- Extracts document structure (Title, H1–H3 headings) in under 10 seconds per PDF.
- Uses multi-factor heading detection (font size, styling, position) via **PyMuPDF**.

### ✅ Round 1B – Persona-Based Document Intelligence
- Upload 3–10 PDFs and input a persona description.
- Ranks document sections by relevance using a **hybrid BM25 + BERT-small** pipeline.
- Includes interactive bar/pie charts and JSON export.

### 🌐 Frontend
- Built with **React** and **Tailwind CSS**
- Drag-and-drop file upload, outline visualization, interactive charts, and progress indicators.

### 🔙 Backend
- REST API with **Flask + Gunicorn**
- Handles file parsing, ranking logic, and PDF processing.
- Runs offline with **CPU-optimized models** — no external APIs.

---

## 🧰 Tech Stack

| Component         | Technology                                        |
|------------------|----------------------------------------------------|
| Frontend         | React, Tailwind CSS, Chart.js                      |
| Backend          | Flask, Gunicorn                                    |
| PDF Parsing      | PyMuPDF (fitz)                                     |
| NLP & Ranking    | spaCy, Sentence Transformers, BERT-small, sklearn BM25 |
| Deployment       | Docker, Heroku, Fly.io                             |
| Storage (opt.)   | JSON or lightweight DB                             |

---

## 📁 Project Structure

```
connecting-the-dots/
├── backend/
│   ├── app.py
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
├── heroku.yml
└── README.md
```

---

## ⚙️ Getting Started

### 🔧 Prerequisites
- Python 3.11+
- Node.js 16+ and npm
- Docker (optional for deployment)

### 🛠 Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run
```

### 🎨 Frontend Setup
```bash
cd frontend
npm install
npm start
```

> React app will proxy to `http://localhost:5000`.

---

## 🧪 Usage

### 🗂 Round 1A – Outline Extraction
1. Go to the **Round 1A** tab.
2. Upload a PDF or use a sample file.
3. View the extracted outline (Title, H1-H3).
4. Export as JSON.

### 🧬 Round 1B – Persona-Driven Intelligence
1. Go to the **Round 1B** tab.
2. Upload 3–10 PDFs.
3. Enter Persona & Job-to-Be-Done.
4. Click **Analyze Documents**.
5. View ranked sections with charts.
6. Export results as JSON.

---

## 🧠 Algorithms

### 🔹 Outline Extraction
- Font size outlier detection
- Bold and numbered heading patterns
- Positional layout on page

### 🔹 Persona Ranking
- Approximate BM25 with TF-IDF
- BERT-small reranking via Sentence Transformers
- Fully offline, CPU-only inference (quantized)

---

## 🚀 Deployment

### 🐳 Local via Docker
```bash
docker-compose up --build
```

### ☁️ Deploy to Heroku
```bash
heroku create connecting-the-dots-demo --buildpack heroku/python
heroku stack:set container
git push heroku main
```

> Backend image <200MB, models cached during build for offline operation.

---

## ✅ Testing

- **Backend**: `pytest` for unit testing (PDF, ranking logic)
- **Frontend**: React Testing Library, Cypress
- **Performance**: 
  - Round 1A: under 10 seconds
  - Round 1B: under 60 seconds (10 PDFs)

---

## 🤝 Contributing

Contributions are welcome!  
Fork the repo → create a branch → submit a pull request.

---

## 📄 License

This project is intended for **educational and hackathon** use.

---

## 🙌 Acknowledgments

- Built for Adobe’s *“Connecting the Dots”* Hackathon.
- Powered by open-source tools: PyMuPDF, spaCy, BERT, Sentence Transformers.

> ⚡ Build a fast, accurate, persona-aware document intelligence system — combining full-stack development and applied AI/ML expertise!