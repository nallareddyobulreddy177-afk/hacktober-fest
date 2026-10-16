
import re
import streamlit as st

from tools import extract_pdf_pages, split_into_chunks, search_chunks
from model import ask_ollama


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# 2. PROFESSIONAL DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}

[data-testid="stSidebar"] {
    background-color: #151923;
    border-right: 1px solid #293142;
}

.hero {
    padding: 28px;
    border-radius: 18px;
    background: linear-gradient(120deg, #182848, #243b55);
    border: 1px solid #34445e;
    margin-bottom: 24px;
}

.hero h1 {
    color: white;
    font-size: 30px;
    margin-bottom: 8px;
}

.hero p {
    color: #c7d5e8;
    font-size: 15px;
    margin-bottom: 0;
}

.stButton button {
    border-radius: 10px;
}

div[data-testid="stChatMessage"] {
    border: 1px solid #293142;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
}

.footer {
    color: #8b98aa;
    text-align: center;
    font-size: 12px;
    padding: 24px 0;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. SESSION STATE
# ==========================================

defaults = {
    "pdf_name": None,
    "file_id": None,
    "pages": [],
    "chunks": [],
    "messages": [],
    "pending_question": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# 4. DATE DETECTION
# ==========================================

def extract_date_facts(pages):
    full_text = "\n".join(
        page["text"] for page in pages
    )

    date_pattern = (
        r"\b(?:"
        r"\d{1,2}[./-]\d{1,2}[./-]\d{4}"
        r"|"
        r"\d{4}-\d{1,2}-\d{1,2}"
        r")\b"
    )

    year_pattern = (
        r"\b(?:19|20)\d{2}\s*[-–/]\s*"
        r"(?:(?:19|20)\d{2}|\d{2})\b"
    )

    dates = list(dict.fromkeys(
        re.findall(date_pattern, full_text)
    ))

    years = list(dict.fromkeys(
        re.findall(year_pattern, full_text)
    ))

    return dates, years


# ==========================================
# 5. SIDEBAR AND PDF UPLOAD
# ==========================================

with st.sidebar:
    st.markdown("## 📚 DocuMind AI")
    st.caption("Your private document workspace")
    st.divider()

    st.markdown("### 📤 Upload document")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
    )

    if uploaded_file is not None:
        file_id = (
            uploaded_file.name,
            uploaded_file.size,
        )

        if st.session_state["file_id"] != file_id:
            try:
                with st.spinner("Reading your PDF..."):
                    pages = extract_pdf_pages(
                        uploaded_file.getvalue()
                    )

                    chunks = split_into_chunks(pages)

                    st.session_state["pdf_name"] = uploaded_file.name
                    st.session_state["file_id"] = file_id
                    st.session_state["pages"] = pages
                    st.session_state["chunks"] = chunks
                    st.session_state["messages"] = []
                    st.session_state["pending_question"] = None

            except Exception as error:
                st.error(f"Could not read PDF: {error}")

    st.divider()
    st.markdown("### 📄 Document information")

    if st.session_state["pdf_name"]:
        st.write(
            f"**File:** {st.session_state['pdf_name']}"
        )

        st.metric(
            "Pages with extracted text",
            len(st.session_state["pages"]),
        )

        st.metric(
            "Text sections",
            len(st.session_state["chunks"]),
        )

        # NEW: Show extracted PDF text
        with st.expander("🔍 View extracted PDF text"):
            for page in st.session_state["pages"]:
                st.write(f"Page {page['page']}")
                st.text(page["text"])

        if st.button(
            "🗑️ Clear document and chat",
            use_container_width=True,
        ):
            for key, value in defaults.items():
                st.session_state[key] = value

            st.rerun()

    else:
        st.info("Upload a PDF to get started.")

    st.divider()
    st.markdown("### 🔒 Privacy")
    st.caption(
        "This app is configured to use your local Ollama model. "
        "Check your configuration if local-only processing "
        "is important to you."
    )


# ==========================================
# 6. MAIN HEADER
# ==========================================

st.markdown("""
<div class="hero">
    <h1>📚 Private AI Document Assistant</h1>
    <p>
        Upload a PDF, ask questions, and find information
        using your local AI model.
    </p>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 7. WELCOME SCREEN
# ==========================================

pages = st.session_state["pages"]
chunks = st.session_state["chunks"]

if not st.session_state["pdf_name"]:
    st.markdown("### 👋 Welcome to DocuMind AI!")

    st.write(
        "Upload a PDF using the sidebar to start chatting "
        "with your document."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📄 Read documents")
        st.caption("Extract text from PDF files.")

    with col2:
        st.markdown("#### 💬 Ask questions")
        st.caption("Find information using document chat.")

    with col3:
        st.markdown("#### 🤖 Local AI")
        st.caption("Generate answers using Ollama.")


# ==========================================
# 8. DOCUMENT CHAT
# ==========================================

elif not chunks:
    st.warning(
        "No readable text was found. Check your PDF "
        "and Tesseract OCR installation."
    )

else:
    st.markdown("### 💬 Document chat")

    st.caption(
        "Answers use extracted PDF text. Verify important "
        "details against the original document."
    )

    st.markdown("**Suggested questions**")

    col1, col2, col3 = st.columns(3)

    suggestions = [
        "What is this document about?",
        "What are the important dates?",
        "Summarize the main details.",
    ]

    for column, suggestion in zip(
        [col1, col2, col3],
        suggestions,
    ):
        with column:
            if st.button(
                suggestion,
                use_container_width=True,
            ):
                st.session_state["pending_question"] = suggestion

    # Show chat history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    typed_question = st.chat_input(
        "Ask a question about your PDF..."
    )

    pending_question = st.session_state.pop(
        "pending_question", None
    )

    question = typed_question or pending_question

    if question:
        st.session_state["messages"].append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching your document..."):

                question_lower = question.lower()

                date_keywords = [
                    "date",
                    "dates",
                    "year",
                    "academic",
                    "admission",
                ]

                asks_about_dates = any(
                    word in question_lower
                    for word in date_keywords
                )

                # Date questions use extracted date patterns
                if asks_about_dates:
                    dates, years = extract_date_facts(pages)

                    if dates or years:
                        answer_parts = []

                        if dates:
                            answer_parts.append(
                                "**Dates found in the extracted text:**\n"
                                + "\n".join(
                                    f"- {date}" for date in dates
                                )
                            )

                        if years:
                            answer_parts.append(
                                "**Year references found:**\n"
                                + "\n".join(
                                    f"- {year}" for year in years
                                )
                            )

                        answer = "\n\n".join(answer_parts)

                        answer += (
                            "\n\nThese are dates found in the text. "
                            "Check the original PDF to confirm "
                            "what each date refers to."
                        )

                    else:
                        answer = None

                else:
                    answer = None

                if answer is None:
                    full_document_keywords = [
                        "document",
                        "summarize",
                        "summary",
                        "important",
                        "fee",
                        "fees",
                        "amount",
                        "total",
                        "cost",
                        "overview",
                    ]

                    use_all_chunks = any(
                        word in question_lower
                        for word in full_document_keywords
                    )

                    if use_all_chunks:
                        relevant_chunks = chunks
                    else:
                        relevant_chunks = search_chunks(
                            question,
                            chunks,
                            top_k=4,
                        )

                    if not relevant_chunks:
                        answer = (
                            "I couldn't find enough relevant text "
                            "to answer this question. Please try "
                            "another question."
                        )
                    else:
                        context = "\n\n".join(
                            f"[Page {chunk['page']}]\n"
                            f"{chunk['text']}"
                            for chunk in relevant_chunks
                        )

                        try:
                            answer = ask_ollama(
                                question,
                                context,
                            )
                        except Exception as error:
                            answer = (
                                "I couldn't get a response from "
                                "your local AI model. Check that "
                                "Ollama is running and the model "
                                "is installed.\n\n"
                                f"Technical details: {error}"
                            )

                st.markdown(answer)

        st.session_state["messages"].append({
            "role": "assistant",
            "content": answer,
        })


# ==========================================
# 9. FOOTER
# ==========================================

st.markdown(
    '<div class="footer">'
    'DocuMind AI · Private AI Document Assistant'
    '</div>',
    unsafe_allow_html=True,
)
