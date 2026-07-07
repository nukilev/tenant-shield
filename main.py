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
                    str_ui.markdown(f"### סעיף {i}")

                    analysis_result_string = analyze_contract_text(chunk)
                    analysis_json = json.loads(analysis_result_string)

                    risk = analysis_json.get('risk_level', 'green').lower()
                    explanation = analysis_json.get('explanation', '')
                    alternative = analysis_json.get('alternative_text', '')

                    if risk == 'red':
                        str_ui.error(f"🚨 **רמת סיכון: אדום (סעיף דרקוני/בעייתי)**\n\n**הסבר:** {explanation}")
                    elif risk == 'yellow':
                        str_ui.warning(f"⚠️ **רמת סיכון: צהוב (דורש תשומת לב)**\n\n**הסבר:** {explanation}")
                    else:
                        str_ui.success(f"✅ **רמת סיכון: ירוק (תקין ומאוזן)**\n\n**הסבר:** {explanation}")

                    if alternative:
                        str_ui.markdown("**הצעה לנוסח חלופי ומאוזן:**")
                        str_ui.code(alternative, language="text")

                    str_ui.markdown("---")

                str_ui.balloons()

            except Exception as e:
                str_ui.error(f"התרחשה שגיאה במהלך הניתוח: {e}")