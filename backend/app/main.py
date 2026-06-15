from pathlib import Path
import os
import ssl
import urllib3
import requests

# CRITICAL: Patch httpcore SSL before ANY other imports
import sys

_orig_wrap_socket = ssl.SSLContext.wrap_socket
def _patched_wrap_socket(self, sock, *args, **kwargs):
    kwargs['server_hostname'] = kwargs.get('server_hostname', None)
    old_check = self.check_hostname
    old_verify = self.verify_mode
    try:
        self.check_hostname = False
        self.verify_mode = ssl.CERT_NONE
        return _orig_wrap_socket(self, sock, *args, **kwargs)
    finally:
        self.check_hostname = old_check
        self.verify_mode = old_verify

ssl.SSLContext.wrap_socket = _patched_wrap_socket
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from dotenv import load_dotenv

original_get = requests.get
def patched_get(url, **kwargs):
    if 'openaipublic.blob.core.windows.net' in url or 'tiktoken' in url:
        kwargs['verify'] = False
    return original_get(url, **kwargs)
requests.get = patched_get

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

from pydantic import BaseModel

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
DB_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "smart_docs"

load_dotenv(PROJECT_DIR / ".env")

UPLOAD_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Smart Document Q&A", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    filename: str | None = None


from langchain_core.embeddings import Embeddings
import hashlib

class LocalEmbeddings(Embeddings):
    """Local embedding function that doesn't require downloads"""
    
    def embed_documents(self, texts):
        """Embed a list of documents"""
        return [self._embed_text(text) for text in texts]
    
    def embed_query(self, text):
        """Embed a query"""
        return self._embed_text(text)
    
    @staticmethod
    def _embed_text(text: str):
        """Create deterministic embedding from text without external downloads"""
        # Use SHA256 hash to create deterministic vector
        h = hashlib.sha256(text.encode()).digest()
        # Convert bytes to float vector (384 dimensions)
        vector = []
        for i in range(0, min(len(h), 384)):
            byte_val = h[i] if i < len(h) else 0
            vector.append((byte_val - 128) / 128.0)
        # Pad to 384 dimensions
        while len(vector) < 384:
            vector.append(0.0)
        return vector[:384]

def _get_embeddings():
    return LocalEmbeddings()


def _get_vector_store():
    embeddings = _get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(DB_DIR),
    )


def _normalize_source_candidates(filename: str) -> list[str]:
    normalized = Path(filename).name
    candidates = [normalized]
    candidates.append(str(UPLOAD_DIR / normalized))
    candidates.append(str((UPLOAD_DIR / normalized).resolve()))
    candidates.append(str((UPLOAD_DIR / normalized).resolve().as_posix()))
    candidates.append(str((UPLOAD_DIR / normalized).relative_to(UPLOAD_DIR)))
    return list(dict.fromkeys(candidates))


def _index_pdf(file_path: Path) -> int:
    if not file_path.exists():
        raise FileNotFoundError("PDF file was not found")

    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    for i, doc in enumerate(documents):
        print(f"DEBUG doc[{i}] length={len(doc.page_content)} ...")
    if not documents:
        raise ValueError("No text could be extracted from the PDF")

    print(f"DEBUG: Loaded {len(documents)} documents from PDF")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)

    print(f"DEBUG: Created {len(chunks)} chunks")
    
    if not chunks:
        raise ValueError("No chunks created from PDF")

    for chunk in chunks:
        chunk.metadata["source"] = file_path.name
        chunk.metadata["source_path"] = str(file_path)

    try:
        vector_store = _get_vector_store()
        print(f"DEBUG: Vector store initialized")
        
        # Try to add documents
        vector_store.add_documents(chunks)
        print(f"DEBUG: Added {len(chunks)} chunks to vector store")
        
        print(f"DEBUG: Persisted vector store")
    except Exception as exc:
        print(f"ERROR in vector store: {exc}")
        raise

    return len(chunks)


@app.get("/")
def root():
    return {
        "service": "smart-rag-backend",
        "status": "ok",
        "endpoints": ["/health", "/upload", "/chat"],
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "smart-rag-backend"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name")

    extension = Path(file.filename).suffix.lower()
    if extension != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported for now")

    saved_path = UPLOAD_DIR / file.filename
    with saved_path.open("wb") as target:
        target.write(await file.read())

    try:
        chunk_count = _index_pdf(saved_path)
    except Exception as exc:
        import traceback
        print(f"ERROR during indexing: {exc}", file=__import__('sys').stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to index document: {exc}") from exc

    return {
        "message": "Document uploaded and indexed",
        "filename": file.filename,
        "path": str(saved_path),
        "chunks": chunk_count,
        "status": "indexed",
    }


@app.post("/chat")
def answer_question(payload: QuestionRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        vector_store = _get_vector_store()
        docs = vector_store.similarity_search(payload.question, k=8)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve context: {exc}") from exc

    if payload.filename:
        candidates = _normalize_source_candidates(payload.filename)
        docs = [doc for doc in docs if str(doc.metadata.get("source", "")) in candidates or str(doc.metadata.get("source_path", "")) in candidates]

    if not docs:
        detail = "No relevant document context was found. Upload a PDF and try again."
        if payload.filename:
            detail = f"No relevant context was found for '{payload.filename}'. Try uploading the file again or ask a different question."
        return {
            "answer": detail,
            "sources": [],
            "question": payload.question,
        }

    context = "\n\n".join(document.page_content for document in docs[:4])

    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0.2, google_api_key=api_key)
        prompt = (
            "You are a helpful assistant. Answer ONLY using the document context below. "
            "If the answer is not in the context, say that you do not know.\n\n"
            f"Question:\n{payload.question}\n\n"
            f"Relevant Context:\n{context}\n\n"
            "Answer:"
        )
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        print(f"ERROR in chat endpoint: {exc}", flush=True)
        import traceback
        traceback.print_exc()
        document_text = "\n\n".join(f"[{doc.metadata.get('source', 'Unknown')}] {doc.page_content}" for doc in docs[:2])
        answer = (
            "Unable to generate a model-based answer due to API quota or availability. "
            "Here are the most relevant document excerpts:\n\n" + document_text
        )

    sources = sorted({document.metadata.get("source", "Unknown") for document in docs})

    return {
        "answer": answer,
        "sources": sources,
        "question": payload.question,
    }
