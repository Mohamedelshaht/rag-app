import streamlit as st
from groq import Groq
import pypdf

st.set_page_config(page_title="مساعد المستندات الذكي", page_icon="📚")
st.title("📚 مساعد المستندات (RAG) باستخدام Groq")

# التحقق من وجود المفتاح وتنظيفه من أي مسافات مخفية
if "GROQ_API_KEY" not in st.secrets:
    st.error("مفتاح GROQ_API_KEY غير مكتوب في Secrets!")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"].strip()
client = Groq(api_key=api_key)

# رفع ملفات PDF
uploaded_files = st.file_uploader("ارفع ملفات PDF الخاصة بك هنا", type=["pdf"], accept_multiple_files=True)

extracted_text = ""
if uploaded_files:
    for pdf_file in uploaded_files:
        pdf_reader = pypdf.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    st.success("تم قراءة الملفات بنجاح!")

# حقل السؤال والدردشة
user_query = st.text_input("اطرح سؤالك حول المستندات:")

if user_query:
    if not extracted_text:
        st.warning("يرجى رفع ملف PDF أولاً لتمكين البحث.")
    else:
        with st.spinner("جاري تحليل السؤال والبحث في الملفات..."):
            system_prompt = f"""
أنت مساعد ذكي يجيب على أسئلة المستخدم بدقة باللغة العربية بناءً على النص المرفق أدناه.
إذا لم تكن الإجابة موجودة بالنص، أبلغ المستخدم بذلك بلياقة.

النص المستخرج من الملفات:
{extracted_text[:12000]}
"""
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.2,
                )
                st.subheader("الإجابة:")
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(f"تفاصيل الخطأ الحقيقية من Groq:\n\n{e}")
