from reportlab.pdfgen import canvas

c = canvas.Canvas('test_document.pdf')
c.drawString(100, 750, 'This is a test PDF')
c.drawString(100, 700, 'Hello World')
c.drawString(100, 650, 'This document is for testing the RAG system')
c.drawString(100, 600, 'Question: What is this document about?')
c.drawString(100, 550, 'Answer: This is a simple test PDF for the Smart Document Q&A system')
c.save()
print('PDF created: test_document.pdf')
