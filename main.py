import time
import json
import asyncio
import streamlit as str_ui
from dotenv import load_dotenv
from src.services.pdf_service import read_pdf_contract
from src.services.chunking_service import split_contract_into_chunks
from src.services.ai_service import analyze_all_chunks_parallel

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

                parallel_results = asyncio.run(analyze_all_chunks_parallel(chunks))

                str_ui.markdown("---")

                for i, result in enumerate(parallel_results, start=1):
                    if "error" in result:
                        str_ui.error(f"שגיאה בניתוח סעיף {i}: {result['error']}")
                        continue

                    original_text = result["original_text"]
                    analysis_json = json.loads(result["analysis"])

                    with str_ui.container():
                        str_ui.markdown(f"### 📍 סעיף {i}")

                        risk = analysis_json.get('risk_level', 'green').lower()
                        explanation = analysis_json.get('explanation', '')
                        alternative = analysis_json.get('alternative_text', '')

                        col_original, col_analysis = str_ui.columns([1, 1.2], gap="large")

                        with col_original:
                            str_ui.markdown("**📄 מתוך החוזה:**")
                            str_ui.info(original_text)

                        with col_analysis:
                            str_ui.markdown("**🔍 ניתוח משפטי:**")
                            if risk == 'red':
                                str_ui.markdown(
                                    "<span style='color:#ef5350; font-weight:bold; font-size:18px;'>🚨 רמת סיכון: אדום</span>",
                                    unsafe_allow_html=True)
                            elif risk == 'yellow':
                                str_ui.markdown(
                                    "<span style='color:#ffca28; font-weight:bold; font-size:18px;'>⚠️ רמת סיכון: צהוב</span>",
                                    unsafe_allow_html=True)
                            else:
                                str_ui.markdown(
                                    "<span style='color:#66bb6a; font-weight:bold; font-size:18px;'>✅ רמת סיכון: ירוק</span>",
                                    unsafe_allow_html=True)

                            str_ui.markdown(f"**הסבר:** {explanation}")

                            if alternative and risk in ['red', 'yellow']:
                                str_ui.markdown("**💡 נוסח חלופי מוצע:**")
                                str_ui.code(alternative, language="text")

                        str_ui.markdown("<hr style='border: 0; height: 1px; background: #e0e0e0; margin: 30px 0;'>",
                                        unsafe_allow_html=True)

                str_ui.balloons()

            except Exception as e:
                str_ui.error(f"התרחשה שגיאה במהלך הניתוח: {e}")