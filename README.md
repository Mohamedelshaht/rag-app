# مساعد المستندات (RAG) — Claude + Streamlit

## الخطوات

### 1) ارفع على GitHub
```bash
git init
git add .
git commit -m "init rag app"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```
> ملف `secrets.toml` متجاهَل في `.gitignore`، ماترفعش المفتاح أبدًا على GitHub.

### 2) انشر على Streamlit Community Cloud
1. ادخل https://share.streamlit.io وسجّل بحساب GitHub.
2. **Create app** ← اختار الريبو والفرع `main` والملف `app.py`.
3. من **Advanced settings ← Secrets** حط:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
CLAUDE_MODEL = "claude-sonnet-5-5"
APP_PASSWORD = "اختياري"
```
4. اضغط **Deploy**. أول تشغيل بياخد دقيقتين (تحميل نموذج التضمين).

### بديل: Hugging Face Spaces
اعمل Space نوع **Streamlit**، واربطه بالريبو، وحط المفتاح في **Settings ← Secrets** باسم `ANTHROPIC_API_KEY`.

## إضافة مستنداتك
حط ملفات PDF/TXT/MD في مجلد `docs/` وارفعها على GitHub، والتطبيق بيعيد الفهرسة تلقائيًا.
