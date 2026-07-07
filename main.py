import json
from dotenv import load_dotenv
from src.services.pdf_service import read_pdf_contract
from src.services.ai_service import analyze_contract_text

# טעינת משתני הסביבה (חובה להשאיר בנקודת הכניסה)
load_dotenv()


def main():
    pdf_filename = "sample_contract.pdf"
    print(f"Starting Tenant Shield on: {pdf_filename}...")

    try:
        # 1. קריאת ה-PDF באמצעות השירות הייעודי
        contract_text = read_pdf_contract(pdf_filename)
        print(f"Successfully extracted {len(contract_text)} characters.")

        # 2. ניתוח באמצעות שירות ה-AI
        print("Sending to Gemini for analysis...")
        analysis_result_string = analyze_contract_text(contract_text)

        # 3. הצגת התוצאה
        analysis_json = json.loads(analysis_result_string)
        print("\n--- Analysis Result ---")
        print(json.dumps(analysis_json, indent=4, ensure_ascii=False))

    except Exception as e:
        print(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    main()