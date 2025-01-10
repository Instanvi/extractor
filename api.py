
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from pdf2image import convert_from_bytes
import pytesseract
import cv2
import numpy as np
from dotenv import load_dotenv
from validators import DocumentValidator
from transformers import pipeline

load_dotenv()
app = FastAPI()


def extract_data(text: str):

    #For offline use
    classifier = pipeline("text-classification", model="databricks/dolly-v2-3b")
    

    #For use of model directly online
    # Hugging Face hosted pipeline
    # pipe = pipeline(
    #     "text-generation",
    #     model="databricks/dolly-v2-3b",
    #     use_auth_token = os.getenv("HUGGING_FACE_TOKEN"),
    #     trust_remote_code=True
    # )

    prompt = f" Take this text: {text}, Organise it and extract data for these fields doc_type, doc_number, issue date,due_date,supplier_name, supplier_address , customer_name,customer_address,total_amount ,tax_amount,line_items. line_items are items purchased and information on them"
    print("into pipeline")
    # response = pipe(prompt)
    response = classifier(prompt)
    print(response[0]["generated_text"])
    print(response)
    return response

@app.post("/process-document/", response_model=DocumentValidator)
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
        print(f"extracted text: {text} \n")

        output = extract_data(text)
        return output



    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))