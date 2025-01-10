from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from pdf2image import convert_from_bytes
import pytesseract
import cv2
import numpy as np
import io
from match_handler import extract_data_from_text
import json

app = FastAPI()



@app.post("/")
async def process_document(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Convert PDF to images if necessary
        if file.filename.endswith('.pdf'):
            images = convert_from_bytes(contents)
            # Process first page for now
            image = np.array(images[0])
        else:
            # Handle image files
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print("image now")
        # Preprocess image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        # Extract text using OCR
        text = pytesseract.image_to_string(processed)
        print(f"extracted text")

        # Extract structured data
        extracted_data = extract_data_from_text(text)
        # print(extracted_data)
        if len(extracted_data) > 0:
            response = json.loads(extracted_data)
        else:
            print("retrying.....")
            extracted_data = extract_data_from_text(text)
            response = json.loads(extracted_data)

        # Save to database
        # doc_dict = document.model_dump()
        # doc_id = await db.insert_document(doc_dict)
        print(response)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
