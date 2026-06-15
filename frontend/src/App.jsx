import { useState } from 'react';

export default function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [fileName, setFileName] = useState('');
  const [statusMessage, setStatusMessage] = useState('בחר PDF והזן שאלה כדי להתחיל.');
  const [loading, setLoading] = useState(false);

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      setStatusMessage('נא לבחור קובץ PDF קודם.');
      return;
    }

    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setStatusMessage('הקובץ חייב להיות PDF בלבד.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setStatusMessage('מעלה מסמך...');

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'העלאה נכשלה.');
      }

      setFileName(data.filename || file.name);
      setAnswer('המסמך הועלה בהצלחה.');
      setStatusMessage(`המסמך "${data.filename || file.name}" נשמר ואינדקסים בהצלחה.`);
    } catch (error) {
      setAnswer('');
      setStatusMessage(error.message || 'אירעה שגיאה בהעלאת המסמך.');
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) {
      setStatusMessage('נא לכתוב שאלה לפני שליחת הבקשה.');
      return;
    }

    if (!fileName) {
      setStatusMessage('נא להעלות PDF קודם לפני השאלה.');
      return;
    }

    setLoading(true);
    setStatusMessage('שואל את המסמך...');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, filename: fileName }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'השאלה נכשלה.');
      }

      setAnswer(data.answer || 'אין תשובה זמינה.');
      setStatusMessage('התשובה נוצרה מתוך המסמך שהועלה.');
    } catch (error) {
      setAnswer('');
      setStatusMessage(error.message || 'אירעה שגיאה בבקשת השאלה.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ fontFamily: 'Arial, sans-serif', padding: 24, maxWidth: 980, margin: '0 auto' }}>
      <h1>Smart Document Q&A</h1>
      <p>מערכת RAG לתשובות מבוססות מסמכים עם FastAPI, ChromaDB ו-OpenAI.</p>

      <section style={{ display: 'grid', gap: 16, marginTop: 24 }}>
        <label style={cardStyle}>
          <strong>1. העלאת מסמך PDF</strong>
          <input type="file" accept="application/pdf" onChange={handleUpload} />
          <small>{fileName ? `קובץ נבחר: ${fileName}` : 'בחר קובץ PDF...'}</small>
        </label>

        <label style={cardStyle}>
          <strong>2. שאלת משתמש</strong>
          <textarea
            rows={4}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="לדוגמה: מהי מדיניות החופשה?"
            style={{ width: '100%', padding: 10, borderRadius: 8, border: '1px solid #ccc' }}
          />
          <button
            onClick={handleAsk}
            disabled={loading || !question.trim() || !fileName}
            style={{ ...buttonStyle, opacity: loading || !question.trim() || !fileName ? 0.6 : 1 }}
          >
            {loading ? 'טוען...' : 'בקש תשובה'}
          </button>
        </label>

        <section style={cardStyle}>
          <strong>3. תשובה</strong>
          <p style={{ color: '#4b5563', marginBottom: 8 }}>{statusMessage}</p>
          <p style={{ whiteSpace: 'pre-wrap', minHeight: 60 }}>{answer || 'התשובה תופיע כאן.'}</p>
        </section>
      </section>
    </main>
  );
}

const cardStyle = {
  display: 'grid',
  gap: 8,
  border: '1px solid #ddd',
  borderRadius: 12,
  padding: 16,
  background: '#fff',
  boxShadow: '0 4px 12px rgba(0,0,0,0.04)',
};

const buttonStyle = {
  padding: '10px 14px',
  border: 'none',
  borderRadius: 8,
  background: '#2563eb',
  color: '#fff',
  cursor: 'pointer',
  width: 'fit-content',
};
