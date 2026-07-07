import time
import json
from dotenv import load_dotenv
from src.services.pdf_service import read_pdf_contract
from src.services.chunking_service import split_contract_into_chunks
from src.services.ai_service import analyze_contract_text

load_dotenv()

def main():
    pdf_filename = "sample_contract.pdf"
    print(f"Starting Tenant Shield on: {pdf_filename}...")

    try:
        # 1. קריאת ה-PDF באמצעות השירות הייעודי
        contract_text = read_pdf_contract(pdf_filename)
        print(f"Successfully extracted {len(contract_text)} characters.")

        chunks = split_contract_into_chunks(contract_text)
        print(f"Contract split into {len(chunks)} individual logical clauses.")

        print("\n--- Starting Clause-by-Clause Analysis (Testing first 3 chunks) ---")

        for i, chunk in enumerate(chunks[:3], start=1):
            print(f"\n[Analyzing Clause {i}/{min(3, len(chunks))}]")
            print(f"Original Text Snippet: {chunk[:60]}...")

            # שליחה ל-AI
            analysis_result_string = analyze_contract_text(chunk)
            analysis_json = json.loads(analysis_result_string)

            # הדפסת התוצאה בצורה יפה
            print(f"Result Risk Level: {analysis_json.get('risk_level').upper()}")
            print(json.dumps(analysis_json, indent=4, ensure_ascii=False))

            # השהייה קלה של שנייה בין בקשות כדי לא לחרוג ממכסות ה-Rate Limit של המסלול החינמי
            time.sleep(1)

    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()