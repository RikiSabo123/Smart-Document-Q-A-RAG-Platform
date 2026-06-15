# Smart Document Q&A System

מערכת RAG להעלאת PDF ולתשובות על פי תוכן המסמך.

## מה זה

פרויקט זה מאפשר להעלות קובץ PDF, לאנדקס אותו ב-ChromaDB, ולשאול שאלות על הטקסט שבמסמך.

## טכנולוגיות

- Backend: FastAPI ו-Python
- Frontend: React ו-Vite
- Vector DB: ChromaDB
- Embeddings: SHA256 מקומי
- LLM: Google Generative AI (Gemini)
- PDF: PyPDF

## מבנה הפרויקט

```
PROJECT/
  backend/
    app/main.py        # שרת FastAPI + RAG pipeline
    uploads/           # קבצי PDF שהועלו
    chroma_db/         # מסד וקטורים
    requirements.txt   # תלותיות Python
  frontend/
    src/App.jsx        # ממשק המשתמש
    src/main.jsx       # כניסת React
    package.json
    vite.config.js     # proxy ל-backend
  docker-compose.yml
  .env                # מפתח GOOGLE_API_KEY
  README.md
```

## התחלה מהירה

### דרישות

- Python 3.11+
- Node.js 18+
- מפתח Google API
- Docker ו-Docker Compose (אופציונלי)

### 1. הגדרת מפתח

בחשבון הפרויקט צור או עדכן את הקובץ `.env` בתיקיית השורש:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 2. הרצת ה-backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

### 3. הרצת ה-frontend

בטרמינל חדש:

```powershell
cd frontend
npm install
npm run dev
```

ברירת המחדל של Vite היא **http://localhost:5173**.

### 4. שימוש

1. פתחו את ה-frontend בדפדפן
2. העלו PDF
3. חכו לאינדוקס
4. כתבו שאלה וקבלו תשובה

## Docker

```powershell
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## נקודות חשובות

- ודאו ש-`GOOGLE_API_KEY` מוגדר ב-`.env`.
- במידה וה-frontend לא מתחבר, בדקו ש-`vite.config.js` מפנה ל-`http://127.0.0.1:8010`.
- אם הקווטה של Gemini נגמרה, המערכת תחזיר קטעי טקסט רלוונטיים מהמסמך.

## קצה ה-API

### `POST /upload`

- מקבל קובץ PDF
- מחזיר שם קובץ ומספר חבילות שנוצרו

### `POST /chat`

- מקבל שאלת טקסט
- ניתן להעביר `filename` כדי להגביל לחיפוש במסמך ספציפי

## בעיות נפוצות

- **העלאת PDF לא עובדת**: ודאו שהקובץ הוא PDF תקין.
- **אין תוצאה רלוונטית**: העלו שוב את המסמך או שאלו בשאלה שונה.
- **Backend לא מתחבר**: ודאו שהשרת רץ ב-8010 ושהפרוקסי ב-frontend נכון.

