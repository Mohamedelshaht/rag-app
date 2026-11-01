import streamlit as st
import os
from groq import Groq
from pypdf import PdfReader

st.set_page_config(page_title="مساعد المستندات الذكي", page_icon="📚")
st.title("📚 مساعد المستندات (RAG) باستخدام Groq")

# جلب المفتاح من Secrets
api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")

if not api_key:
    api_key = st.text_input("أدخل Groq API Key:", type="password")

if api_key:
    client = Groq(api_key=api_key)

    # رفع المستندات
    uploaded_files = st.file_uploader("ارفع ملفات PDF الخاصة بك هنا", type=["pdf"], accept_multiple_files=True)
    
    extracted_text = ""
    if uploaded_files:
        for file in uploaded_files:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() or ""
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
                إذا لم تكن الإجابة موجودة بالنص، أبلغ المستخدم بذلك بلباقة.

                النص المستخرج من الملفات:
                {extracted_text[:12000]}
                """

                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ],
                    temperature=0.2,
                )

                st.subheader("الإجابة:")
                st.write(response.choices[0].message.content)
else:
    st.info("يرجى إدخال Groq API Key للبدء.")
