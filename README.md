# Health Education Extractor

An intelligent tool to automatically extract educational health content from healthcare-related PDFs, structure it into JSON format, and make it ready for ingestion into health app databases. Designed specifically for low-literacy users dealing with food insecurity and chronic conditions.

## 🎯 Purpose

- Extract **relevant, readable, and medically accurate** information from health PDFs
- **Simplify** content into digestible articles for people with low literacy (6th grade reading level)
- Format each entry into a **standard JSON object** compatible with health apps
- Tag articles by **category** and **medical conditions**
- Avoid generating **duplicate content** through intelligent deduplication

## 🏗️ Architecture

### Current Implementation (Phase 1 - MVP)

```
health-education-extractor/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   │   ├── pdf_processing.py    # PDF upload/processing endpoints
│   │   │   └── health_articles.py   # Article management endpoints
│   │   ├── core/              # Core application components
│   │   │   └── database.py    # Database connection setup
│   │   ├── models/            # Data models
│   │   │   ├── health_article.py    # Health article model
│   │   │   └── pdf_document.py      # PDF document model
│   │   ├── services/          # Business logic services
│   │   │   └── pdf_parser.py  # PDF content extraction
│   │   └── main.py           # FastAPI application entry point
│   ├── config.py             # Configuration management
│   └── requirements.txt      # Python dependencies
├── frontend/                  # Next.js frontend (Phase 2)
├── data/                     # Data storage
│   ├── uploads/              # Uploaded PDF files
│   ├── exports/              # Generated JSON exports
│   └── processed/            # Processed content
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

### Tech Stack

- **Backend**: Python 3.9+, FastAPI, Uvicorn
- **Database**: MongoDB with Beanie ODM
- **PDF Processing**: PyMuPDF (fitz)
- **AI/ML**: Google Gemini Pro API, FAISS/ChromaDB for embeddings
- **Image Search**: Unsplash API
- **Frontend**: Next.js + TailwindCSS (Phase 2)

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- MongoDB (local or cloud)
- Google Gemini API key
- Unsplash API key

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd health-education-extractor
   ```

2. **Set up Python environment**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the project root:

   ```env
   # Database Configuration
   MONGODB_URL=mongodb://localhost:27017
   MONGODB_DB_NAME=health_education_extractor

   # App Database Configuration (for published articles)
   # Note: APP_MONGODB_URL uses the same connection as MONGODB_URL
   APP_MONGODB_DB_NAME=test

   # Google AI (Gemini) API
   GEMINI_API_KEY=your_gemini_api_key_here

   # Image APIs
   UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
   UNSPLASH_SECRET_KEY=your_unsplash_secret_key_here

   # Application Settings
   DEBUG=True
   LOG_LEVEL=INFO
   MAX_FILE_SIZE_MB=50
   CHUNK_SIZE_WORDS=200

   # Processing Settings
   SIMILARITY_THRESHOLD=0.85
   MAX_IMAGES_PER_ARTICLE=1
   READING_LEVEL_TARGET=6

   # Server Configuration
   HOST=0.0.0.0
   PORT=8000
   ```

4. **Start MongoDB**
   Make sure MongoDB is running locally or configure connection to cloud instance.

5. **Run the application**

   ```bash
   cd backend
   source venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

   The API will be available at `http://localhost:8000`

   - Interactive API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

## 📋 API Endpoints

### PDF Processing

- `POST /api/v1/pdf/upload` - Upload PDF for processing
- `GET /api/v1/pdf/status/{pdf_id}` - Get processing status
- `GET /api/v1/pdf/list` - List all PDFs with pagination
- `DELETE /api/v1/pdf/{pdf_id}` - Delete PDF and associated data

### Health Articles

- `POST /api/v1/articles/` - Create new article
- `GET /api/v1/articles/` - List articles with filtering
- `GET /api/v1/articles/{article_id}` - Get specific article
- `PUT /api/v1/articles/{article_id}` - Update article
- `DELETE /api/v1/articles/{article_id}` - Delete article
- `POST /api/v1/articles/{article_id}/approve` - Approve article and upload to app database
- `POST /api/v1/articles/{article_id}/reject` - Reject article
- `POST /api/v1/articles/upload-to-app-database` - Upload approved articles to app database
- `GET /api/v1/articles/export/summary` - Get export summary statistics

## 🔄 Processing Pipeline

1. **PDF Upload** - User uploads healthcare PDF via API
2. **Text Extraction** - PyMuPDF extracts text, images, and structure
3. **Content Chunking** - Split into logical units (~150-300 words)
4. **Relevance Filtering** - Filter health-related content
5. **LLM Summarization** - Gemini Pro simplifies to 6th grade level
6. **Image Matching** - Unsplash API finds relevant images
7. **Duplicate Detection** - FAISS/ChromaDB prevents duplicates
8. **Article Generation** - Create structured JSON output
9. **Review & Approval** - Human review and approval workflow
10. **App Database Upload** - Approved articles automatically uploaded to app database

### Example Output

```json
{
  "title": "Understanding High Blood Pressure",
  "category": "Hypertension",
  "imageUrl": "https://images.unsplash.com/photo-1685485276224-d78ce78f3b95",
  "medicalConditionTags": ["Hypertension"],
  "content": "High blood pressure means the blood pushes too hard on your blood vessels. It can hurt your heart, kidneys, brain, and eyes — even if you feel fine.\n\nWhy it matters:\n- It usually has no signs\n- It can last a lifetime\n- It raises your risk for stroke and heart disease\n\nWhat helps:\n- Eat less salt\n- Be active most days\n- Stay at a healthy weight\n- Take your medicine if prescribed"
}
```

## 🧪 Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Formatting

```bash
black backend/app/
flake8 backend/app/
```

### Database Models

- **HealthArticle**: Stores processed health articles
- **PDFDocument**: Tracks uploaded PDFs and processing status

## 🛣️ Roadmap

### Phase 1 - MVP ✅

- [x] PDF upload & parsing
- [x] Basic FastAPI structure
- [x] MongoDB integration
- [x] Data models
- [x] Content chunking service
- [x] Gemini LLM integration
- [x] Image search integration
- [x] Duplicate detection
- [x] JSON export functionality
- [x] Complete processing pipeline

### Phase 2 - Admin UI

- [x] Next.js frontend dashboard
- [x] PDF upload interface
- [x] Article review/approval system
- [x] Content management interface

### Phase 3 - Advanced Features

- [ ] Automated monitoring for new files
- [ ] Multi-condition support (CKD, asthma)
- [ ] Enhanced image quality checks
- [ ] Batch processing interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For questions or issues, please [create an issue](link-to-issues) or contact the development team.
