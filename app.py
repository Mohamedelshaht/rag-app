import streamlit as st
from groq import Groq
import pypdf

st.set_page_config(page_title="مساعد المستندات الذكي", page_icon="📚")
st.title("📚 مساعد المستندات (RAG) باستخدام Groq")

# الاتصال بالمفتاح
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
            # التجربة المتتالية للنماذج المتاحة
            models_to_try = [
                "llama3-8b-8192",
                "llama-3.1-8b-instant",
                "llama3-70b-8192",
                "mixtral-8x7b-32768",
                "gemma2-9b-it"
            ]

            response = None
            last_error = None
            for model_name in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_query}
                        ],
                        temperature=0.2,
                    )
                    break
                except Exception as e:
                    last_error = e
                    continue

            if response:
                st.subheader("الإجابة:")
                st.write(response.choices[0].message.content)
            else:
                st.error(f"حدث خطأ أثناء الاتصال بالنماذج:\n\n{last_error}")
