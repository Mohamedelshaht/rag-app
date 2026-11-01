import streamlit as st
from groq import Groq
import pypdf
import docx
import io

st.set_page_config(
    page_title="مساعد المستندات الذكي",
    page_icon="📚"
)

st.title("📚 مساعد المستندات (RAG) - PDF & Word")

# 1. التحقق من وجود المفتاح
if "GROQ_API_KEY" not in st.secrets:
    st.error("مفتاح GROQ_API_KEY غير مكتوب في Secrets!")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"].strip()
client = Groq(api_key=api_key)


# 2. استخراج النصوص من PDF
def extract_text_from_pdf(file):
    text = ""

    try:
        pdf_bytes = io.BytesIO(file.getvalue())
        pdf_reader = pypdf.PdfReader(pdf_bytes)

        for page in pdf_reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        st.error(f"خطأ في قراءة ملف PDF ({file.name}): {e}")

    return text


# 3. استخراج النصوص من Word
def extract_text_from_docx(file):
    text = ""

    try:
        docx_bytes = io.BytesIO(file.getvalue())
        doc = docx.Document(docx_bytes)

        full_text = [
            para.text
            for para in doc.paragraphs
            if para.text
        ]

        text = "\n".join(full_text)

    except Exception as e:
        st.error(
            f"تعذر قراءة ملف Word ({file.name}): {e}"
        )

    return text


# 4. رفع الملفات
uploaded_files = st.file_uploader(
    "ارفع ملفاتك هنا (PDF أو Word بصيغة docx)",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

extracted_text = ""

if uploaded_files:

    for file in uploaded_files:

        if file.name.lower().endswith(".pdf"):
            extracted_text += (
                extract_text_from_pdf(file) + "\n"
            )

        elif file.name.lower().endswith(".docx"):
            extracted_text += (
                extract_text_from_docx(file) + "\n"
            )

    if extracted_text.strip():
        st.success(
            "تم قراءة واستخراج النصوص من الملفات بنجاح!"
        )

        with st.expander("معاينة النص المستخرج"):
            st.text(extracted_text[:2000])


# 5. حقل السؤال
user_query = st.text_input(
    "اطرح سؤالك حول المستندات:"
)


# 6. معالجة السؤال باستخدام Groq
if user_query:

    if not extracted_text.strip():

        st.warning(
            "يرجى رفع ملف PDF أو Word يحتوي على نص أولاً."
        )

    else:

        with st.spinner(
            "جاري تحليل السؤال والبحث في الملفات..."
        ):

            system_prompt = f"""
أنت مساعد ذكي متخصص في تحليل المستندات.

تعليماتك:
1. أجب باللغة العربية.
2. اعتمد على المعلومات الموجودة في المستندات فقط.
3. أجب بدقة ووضوح.
4. إذا لم تجد الإجابة في المستندات، أخبر المستخدم بذلك.
5. لا تخترع معلومات غير موجودة في الملفات.

النص المستخرج من الملفات:

{extracted_text[:12000]}
"""

            # النماذج المدعومة حاليًا
            models_to_try = [
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b"
            ]

            response = None
            last_error = None

            # تجربة النماذج بالتتابع
            for model_name in models_to_try:

                try:

                    response = client.chat.completions.create(
                        model=model_name,

                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_query
                            }
                        ],

                        temperature=0.2
                    )

                    break

                except Exception as e:

                    last_error = e
                    continue

            # عرض الإجابة
            if response:

                st.subheader("الإجابة:")

                st.write(
                    response.choices[0].message.content
                )

            else:

                st.error(
                    "حدث خطأ أثناء الاتصال بالنماذج:"
                )

                st.code(str(last_error))
