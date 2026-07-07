import time
import json
import streamlit as str_ui
from dotenv import load_dotenv
from src.services.pdf_service import read_pdf_contract
from src.services.chunking_service import split_contract_into_chunks
from src.services.ai_service import analyze_contract_text

load_dotenv()

str_ui.set_page_config(page_title="Tenant Shield - מגן השוכר", layout="centered")

str_ui.markdown(
    """
    <style>
    .stApp { direction: RTL; text-align: right; }
    </style>
    """,
    unsafe_allow_html=True
)

str_ui.title("🛡️ Tenant Shield - מגן השוכר")
str_ui.subheader("ניתוח חוזי שכירות מבוסס AI בזמן אמת")
str_ui.write("העלה את קובץ ה-PDF של חוזה השכירות שלך, והמערכת תציף סיכונים ותציע ניסוחים חלופיים.")

uploaded_file = str_ui.file_uploader("בחר קובץ חוזה שכירות (PDF)", type=["pdf"])

if uploaded_file is not None:
    # שמירה זמנית של הקובץ המועלה כדי שספריית ה-PDF תוכל לקרוא אותו
    temp_filename = "temp_uploaded_contract.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    str_ui.success("📊 הקובץ הועלה בהצלחה! מוכן לניתוח.")

    # כפתור להרצת הניתוח
    if str_ui.button("התחל ניתוח חוזה"):
        with str_ui.spinner("מחלץ טקסט ומנתח סעיפים מול Gemini API..."):
            try:
                # א. חילוץ ופיצול
                full_text = read_pdf_contract(temp_filename)
                chunks = split_contract_into_chunks(full_text)

                str_ui.info(f"החוזה פוצל בהצלחה ל-{len(chunks)} סעיפים לוגיים. מציג את הסעיפים הראשונים:")

                # ב. לולאת ניתוח והצגה בממשק (כרגע מוגבל ל-3 הראשונים לצורך בדיקה מהירה)
                for i, chunk in enumerate(chunks[:3], start=1):

                    # יצירת מסגרת מעוצבת לכל סעיף
                    with str_ui.container():
                        str_ui.markdown(f"### 📍 סעיף {i}")

                        # הרצת הניתוח מול ה-AI
                        analysis_result_string = analyze_contract_text(chunk)
                        analysis_json = json.loads(analysis_result_string)

                        risk = analysis_json.get('risk_level', 'green').lower()
                        explanation = analysis_json.get('explanation', '')
                        alternative = analysis_json.get('alternative_text', '')

                        # חלוקת המסך לשני טורים: ימין (הטקסט המקורי), שמאל (הניתוח)
                        col_original, col_analysis = str_ui.columns([1, 1.2], gap="large")

                        with col_original:
                            str_ui.markdown("**📄 הטקסט המקורי בחוזה:**")
                            # הצגת הטקסט המקורי בתוך תיבה אפורה עדינה כדי להפריד אותו מהניתוח
                            str_ui.info(chunk)

                        with col_analysis:
                            str_ui.markdown("**🔍 ניתוח משפטי וסיכונים:**")

                            # הצגת כותרת סיכון צבעונית ומותאמת
                            if risk == 'red':
                                str_ui.markdown(
                                    "<span style='color:#ef5350; font-weight:bold; font-size:18px;'>🚨 רמת סיכון: אדום (סעיף דרקוני)</span>",
                                    unsafe_allow_html=True)
                                str_ui.markdown(f"**הסבר:** {explanation}")
                            elif risk == 'yellow':
                                str_ui.markdown(
                                    "<span style='color:#ffca28; font-weight:bold; font-size:18px;'>⚠️ רמת סיכון: צהוב (לשים לב)</span>",
                                    unsafe_allow_html=True)
                                str_ui.markdown(f"**הסבר:** {explanation}")
                            else:
                                str_ui.markdown(
                                    "<span style='color:#66bb6a; font-weight:bold; font-size:18px;'>✅ רמת סיכון: ירוק (סטנדרטי)</span>",
                                    unsafe_allow_html=True)
                                str_ui.markdown(f"**הסבר:** {explanation}")

                            # הצגת הנוסח החלופי בתיבת קוד נקייה רק אם יש צורך בשינוי
                            if alternative and risk in ['red', 'yellow']:
                                str_ui.markdown("<br>**💡 הצעה לנוסח חלופי ומאוזן:**", unsafe_allow_html=True)
                                str_ui.code(alternative, language="text")

                        # קו מפריד מעוצב בין סעיף לסעיף
                        str_ui.markdown("<hr style='border: 0; height: 1px; background: #e0e0e0; margin: 30px 0;'>",
                                        unsafe_allow_html=True)
                str_ui.balloons()

            except Exception as e:
                str_ui.error(f"התרחשה שגיאה במהלך הניתוח: {e}")