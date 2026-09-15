import asyncio
import os
import streamlit as st
from google import genai
from dotenv import load_dotenv

from src.services.ai_service import analyze_clause_with_rag, analyze_full_contract
from src.services.contract_parser import extract_text_from_file, split_contract_into_clauses

load_dotenv(override=True)

st.set_page_config(page_title="Tenant Shield - מגן השוכר", layout="wide", page_icon="🛡️")

st.title("🛡️ Tenant Shield - מגן השוכר")
st.caption("מערכת AI ו-RAG לניתוח ובדיקת חוזי שכירות מול הדין הישראלי")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("לא נמצא GEMINI_API_KEY בקובץ ה-.env")
    st.stop()

client = genai.Client(api_key=api_key)

tab_upload, tab_single = st.tabs(["📄 העלאת חוזה מלא (PDF / Word)", "✍️ בדיקת סעיף בודד"])

# -------------------------------------------------------------
# טאב 1: העלאת חוזה מלא
# -------------------------------------------------------------
with tab_upload:
    st.subheader("העלאת קובץ החוזה")
    uploaded_file = st.file_uploader(
        "בחר קובץ חוזה שכירות לבדיקה:",
        type=["pdf", "docx", "txt"],
        help="תומך ב-PDF סרוק דיגיטלית, מסמכי Word וקבצי טקסט"
    )

    if uploaded_file is not None:
        raw_text = extract_text_from_file(uploaded_file)
        clauses = split_contract_into_clauses(raw_text)

        st.info(f"המסמך נקרא בהצלחה: זוהו **{len(clauses)}** סעיפים ומקטעים לניתוח.")

        if st.button("🚀 נתח את כל סעיפי החוזה", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()


            def update_progress(current, total):
                progress_bar.progress(current / total)
                status_text.text(f"מנתח סעיף {current} מתוך {total} מול מאגר החקיקה...")


            results = asyncio.run(analyze_full_contract(client, clauses, update_progress))
            status_text.text("✅ הניתוח הושלם בהצלחה!")

            # סיכום מספרי של הסיכונים
            reds = [r for r in results if r["analysis"].get("risk") == "red"]
            yellows = [r for r in results if r["analysis"].get("risk") == "yellow"]
            greens = [r for r in results if r["analysis"].get("risk") == "green"]

            st.divider()
            st.subheader("📊 תמונת מצב של החוזה")
            m1, m2, m3 = st.columns(3)
            m1.metric("🚨 סעיפים בסיכון גבוה (סותרים חוק)", len(reds))
            m2.metric("⚠️ סעיפים דורשי הבהרה / גבוליים", len(yellows))
            m3.metric("✅ סעיפים תקינים", len(greens))

            st.divider()
            st.subheader("📋 פירוט הניתוח סעיף אחר סעיף")

            for idx, res in enumerate(results, start=1):
                analysis = res["analysis"]
                risk = analysis.get("risk", "green")
                summary = analysis.get("summary", "ניתוח סעיף")

                if risk == "red":
                    box_title = f"🚨 סעיף {idx} [סיכון גבוה]: {summary}"
                elif risk == "yellow":
                    box_title = f"⚠️ סעיף {idx} [סיכון בינוני]: {summary}"
                else:
                    box_title = f"✅ סעיף {idx} [תקין]: {summary}"

                with st.expander(box_title, expanded=(risk == "red")):
                    st.markdown("**נוסח הסעיף בחוזה:**")
                    st.code(res["clause_text"], language="text")

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**⚖️ נימוק משפטי:**")
                        st.write(analysis.get("legal_reasoning"))
                        st.info(f"**מקור חוקי:** {analysis.get('cited_laws')}")
                    with c2:
                        st.markdown("**💡 המלצה מעשית לשוכר:**")
                        st.write(analysis.get("recommendation"))

                    if res.get("retrieved_context"):
                        with st.expander("🔍 צפה בסעיפי החוק המלאים שנשלפו מ-ChromaDB"):
                            st.markdown(res["retrieved_context"])

# -------------------------------------------------------------
# טאב 2: בדיקת סעיף בודד
# -------------------------------------------------------------
with tab_single:
    st.subheader("בדיקת סעיף בודד")
    contract_text = st.text_area(
        "הדבק כאן סעיף מתוך החוזה:",
        height=150,
        placeholder="לדוגמה: השוכר יישא בעלות תיקון כל קלקול במזגן..."
    )

    if st.button("בדוק סעיף", type="primary"):
        if not contract_text.strip():
            st.warning("אנא הזן טקסט.")
        else:
            with st.spinner("שולף סעיפי חוק ומנתח..."):
                result = asyncio.run(analyze_clause_with_rag(client, contract_text))
                analysis = result["analysis"]
                risk = analysis.get("risk", "green")

                if risk == "red":
                    st.error(f"🚨 **סיכון גבוה**: {analysis.get('summary')}")
                elif risk == "yellow":
                    st.warning(f"⚠️ **דורש הבהרה**: {analysis.get('summary')}")
                else:
                    st.success(f"✅ **תקין**: {analysis.get('summary')}")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("⚖️ ניתוח משפטי")
                    st.write(analysis.get("legal_reasoning"))
                    st.info(f"**סעיף החוק שהופעל:** {analysis.get('cited_laws')}")

                with col2:
                    st.subheader("💡 המלצה לשוכר")
                    st.write(analysis.get("recommendation"))

                with st.expander("🔍 צפה בסעיפי החוק המלאים שנשלפו מהמאגר המקומי"):
                    st.markdown(result["retrieved_context"])