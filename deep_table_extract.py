from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
import numpy as np
import pandas as pd
import os

def extract_tables_from_pdf(pdf_bytes):
    """
    Extract tables from a PDF using PaddleOCR's predict() API (recommended for structure/table extraction).
    Args:
        pdf_bytes (bytes): PDF file content as bytes.
    Returns:
        List[dict]: List of tables with page, columns, and rows.
    """
    ocr = PaddleOCR(lang='en', use_textline_orientation=False, use_doc_orientation_classify=False, use_doc_unwarping=False)
    images = convert_from_bytes(pdf_bytes, dpi=300)
    all_tables = []
    for page_num, img_pil in enumerate(images, 1):
        print(f"Processing page {page_num} with PaddleOCR (predict API)...")
        # Save image temporarily because predict() expects a file path
        temp_img_path = f"temp_page_{page_num}.png"
        img_pil.save(temp_img_path)
        try:
            prediction_results = ocr.predict(temp_img_path)
            if not prediction_results:
                print(f"No tables found on page {page_num} (predict returned empty).")
                continue
            for i, res_obj in enumerate(prediction_results):
                # Extract table text from OCRResult object
                item_text = None
                if hasattr(res_obj, 'json') and isinstance(res_obj.json, dict):
                    json_data = res_obj.json
                    if 'res' in json_data and isinstance(json_data['res'], dict):
                        res_content = json_data['res']
                        if 'rec_texts' in res_content and isinstance(res_content['rec_texts'], list):
                            meaningful_texts = [text for text in res_content['rec_texts'] if isinstance(text, str) and text.strip()]
                            if meaningful_texts:
                                # Try to parse as table (split by lines and columns)
                                rows = [row.split('\t') for row in meaningful_texts]
                                df = pd.DataFrame(rows)
                                all_tables.append({
                                    'table': len(all_tables)+1,
                                    'page': page_num,
                                    'columns': df.columns.tolist(),
                                    'rows': df.to_dict(orient='records')
                                })
                                print(f"Table extracted from page {page_num}, result {i+1}.")
                            else:
                                print(f"No meaningful text found in result {i+1} on page {page_num}.")
                        else:
                            print(f"'rec_texts' not found or not a list in result {i+1} on page {page_num}.")
                    else:
                        print(f"'res' not found or not a dict in result {i+1} on page {page_num}.")
                else:
                    print(f"Result object {i+1} does not have .json attribute or it's not a dict.")
        finally:
            # Clean up temp image file
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
    return all_tables
