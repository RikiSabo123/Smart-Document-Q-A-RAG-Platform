# RAG-Based Smart Document Q&A Platform

An AI-powered Retrieval-Augmented Generation (RAG) system that allows users to upload PDF documents and ask questions based on their content.

---

## Overview

The application extracts text from uploaded PDF files, creates embeddings, stores them inside ChromaDB, retrieves relevant document chunks, and generates accurate answers using Google's Gemini model.

---

## Features

- PDF upload
- Automatic document indexing
- Semantic search
- ChromaDB vector database
- Context-aware AI answers
- React frontend
- FastAPI backend
- Docker support

---

## Tech Stack

### Frontend

- React
- Vite

### Backend

- Python
- FastAPI
- LangChain

### Vector Database

- ChromaDB

### AI

- Google Gemini API

### PDF Processing

- PyPDF

---

## Architecture

```
PDF Upload
      │
      ▼
Text Extraction
      │
      ▼
Chunking
      │
      ▼
Embeddings
      │
      ▼
ChromaDB
      │
      ▼
Retriever
      │
      ▼
Gemini
      │
      ▼
Answer
```

---

## Installation

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## API Endpoints

POST /upload

Upload a PDF document.

POST /chat

Ask a question about uploaded documents.

---

## Future Improvements

- Multiple document collections
- Authentication
- Conversation history
- Streaming responses

---

## License

MIT
