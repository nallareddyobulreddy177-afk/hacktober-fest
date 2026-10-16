
import ollama

MODEL_NAME = "llama3.2:1b"


def ask_ollama(question, context):
    prompt = f"""
You are DocuMind AI, a careful PDF assistant.

Answer the user's question using ONLY the supplied PDF text.

RULES:
1. Read all the supplied text before answering.
2. Answer in simple English.
3. For date questions, look for dates written in formats
   such as DD.MM.YYYY, DD/MM/YYYY, or YYYY-MM-DD.
4. If an academic year is present, report it exactly.
5. Do not confuse a certificate date with an admission date.
6. Never invent dates, fee amounts, names, or facts.
7. For fee tables with confusing or mixed-up rows,
   explain that the category and amount cannot be matched
   reliably. Do not guess.
8. Keep optional bus and hostel fees separate from
   the main course fee.
9. If the answer is missing, say:
   "This information is not clearly available in the
   extracted text."
10. Include the PDF page number when provided in the context.

PDF TEXT:
<context>
{context}
</context>

USER QUESTION:
{question}

Give a direct answer supported by the PDF text.
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"]
