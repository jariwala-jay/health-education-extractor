# Product Requirements Document (PRD)

## Project Title:

**Health Education Snippet Extractor from PDFs**

---

## Overview:

We are building a tool to automatically extract educational health content from healthcare-related PDFs, structure it into a specific JSON schema, and make it readily usable for ingestion into a health app database. This content is geared towards low-literacy users dealing with food insecurity and chronic conditions.

---

## Purpose:

The tool's primary purpose is to:

- Extract **relevant, readable, and medically accurate** information from health PDFs
- **Simplify** it into digestible articles for people with low literacy
- Format each entry into a **standard JSON object** compatible with our app
- Tag each article by **category** and **medical conditions**
- Avoid generating **duplicate content** already in the database

---

## End Goals:

1. Streamline ingestion of vetted public health materials (like NIH DASH) into our database.
2. Save time and ensure consistency when preparing app content for chronic disease education.
3. Allow future expansion into other conditions (e.g., asthma, CKD).
4. Prepare this tool to eventually work as an internal API/microservice callable via an admin interface.

---

## Key Features:

### 1. PDF Upload & Parsing

- Upload healthcare PDFs via Web UI
- Extract text and images if available
- Detect and preserve structure (headings, bullet points)

### 2. Chunking & Relevance Filtering

- Automatically chunk long PDFs into logical units (\~150-300 words)
- Filter out tables of contents, references, etc.
- Identify chunks relevant to **health behavior change, condition education, nutrition**

### 3. LLM-Powered Content Summarization

- Run each chunk through a Gemini Pro prompt to:
  - Simplify language to 6th grade reading level
  - Format in JSON with: `title`, `category`, `imageUrl`, `medicalConditionTags`, `content`
  - Keep tone friendly and culturally neutral

### 4. Auto-Image Matching (Unsplash/Open Access)

- Extract keywords from each summary using LLM or rule-based taggers
- Use those keywords to search **Unsplash API** or **Pixabay**
- Select the top result based on relevance and safe-content filtering
- Validate that the license is free for commercial use (e.g. CC0 or Unsplash license)
- Automatically populate the `imageUrl` field

### 5. Duplication Detection

- Compare newly generated articles to existing entries in **MongoDB database**
- Use Gemini embeddings + FAISS/ChromaDB
- Alert if similar article already exists
- Option to keep/edit/skip

### 6. Review Dashboard (Phase 2)

- Human-in-the-loop interface to approve/edit suggested snippets

### 7. Export/Save

- Export JSON file per batch
- Auto-upload to a database endpoint (MongoDB)

---

## Technical Stack:

### Backend

- **Python** for core processing
- **FastAPI** for backend endpoints
- **Gemini Pro API** for LLM summarization and embedding
- **PyMuPDF** or `pdfplumber` for PDF parsing
- **MongoDB** for storing outputs and duplicate checking
- **FAISS** or **ChromaDB** for duplication detection
- **Unsplash API** (fallback: Pexels or Pixabay) for image fetching

### Frontend (Phase 2)

- **Next.js** for admin UI (upload, review, approve)
- **TailwindCSS** for styling
- **shadcn/ui** or **Material UI** for components

### DevOps

- Dockerized container for deployment
- Hosted on **Vercel (frontend)** + **Railway or Render (backend)**
- **Sentry** for error logging

---

## Milestones & Tasks:

### Phase 1 - MVP (2 weeks)

1. PDF upload & parsing module
2. Chunker module with relevance filtering
3. Gemini prompt template for summarization
4. JSON schema formatter
5. Unsplash image search integration (basic keyword match)
6. FAISS/ChromaDB embedding + MongoDB duplicate checker
7. Output JSON preview + download

### Phase 2 - Admin UI (2 weeks)

1. Web dashboard to upload and manage PDFs
2. Article review/edit/approval interface
3. Tag-based search and filtering
4. JSON schema validator
5. Admin sign-in with Firebase/Auth0

### Phase 3 - Automation & Expansion

1. Background cron to watch Drive/Dropbox for new files
2. Prompt tuning for other conditions (CKD, asthma)
3. Add image quality and diversity checks (e.g., faces vs food)
4. Batch approval/export interface

---

## Constraints:

- Uploaded PDFs may have inconsistent formatting
- Generated content must be medically safe and clearly written
- Free-use image selection must respect licensing terms

---

## Success Metrics:

- 95% of articles pass health educator QA
- 90% image match relevance pass rate (visual + content)
- Duplicate rate <5% after filtering
- <30s per article processing time (incl. image and GPT call)

---

Example Response:

{
  "title": "Understanding High Blood Pressure",
  "category": "Hypertension",
  "imageUrl": "https://images.unsplash.com/photo-1685485276224-d78ce78f3b95",
  "medicalConditionTags": ["Hypertension"],
  "content": "High blood pressure means the blood pushes too hard on your blood vessels. It can hurt your heart, kidneys, brain, and eyes — even if you feel fine.\n\nWhy it matters:\n- It usually has no signs\n- It can last a lifetime\n- It raises your risk for stroke and heart disease\n\nWhat helps:\n- Eat less salt\n- Be active most days\n- Stay at a healthy weight\n- Take your medicine if prescribed"
}


