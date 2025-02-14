from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pdf2image import convert_from_bytes
import pytesseract
from pymongo import MongoClient
import cv2
import numpy as np
from match_handler import extract_data_from_text
from data_extractor import extract_text_from_pdf
from database import DataHandler
from potta_handler import equalizer
import json
import os
import logging
import imghdr
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_db_client():
    global client
    global doc_inserter
    client = MongoClient(os.environ["MONGO_URI"])
    
    doc_inserter = DataHandler(
        client= client,
        database_name= os.environ["DB_NAME"],
        collection_name= os.environ["EXT_COLLECTION"]
    )

    # print("MongoDB client initialized")
    logger.info(f"MongoDB client initialized")

# Shutdown event: Close MongoDB connection
@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        logger.info(f"MongoDB client closed")



@app.post("/supplier")
async def process_document(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Convert PDF to images if necessary
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(contents)
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
        print(f"extracted text\n")

        # Extract structured data
        extracted_data = extract_data_from_text(text)
        print(f'extracted data; {extracted_data}\n')
        print(len(extracted_data))
        if len(extracted_data) > 0:
            response = json.loads(extracted_data)
            document = {
                "text": text,
                "label": response
            }
            doc_id = doc_inserter.insert_document(document)

        else:
            print("retrying.....")
            extracted_data = extract_data_from_text(text)

            if len(extracted_data) == 0:
                error_response = {
                    "status": "error",
                    "code": 400,
                    "message": "file sent does not contain the relevant financial data required",
                    "details": {
                        "reason": "No financial data found in the file." 
                    },
                }
                return JSONResponse(status_code=400, content=error_response)
            
            response = json.loads(extracted_data)

        # Save to database
        # doc_dict = document.model_dump()
        # doc_id = await db.insert_document(doc_dict)
        
        
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/supplier/potta")
async def process_potta(file: UploadFile = File(...)):
    try:
        ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/jpg"}
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="File is not an acceptable image (invalid MIME type)")

        # Optional: Check file extension
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise HTTPException(status_code=400, detail="File is not an image (invalid file extension)")
        
        contents = await file.read()
        image_type = imghdr.what(None, contents)
        if not image_type:
            raise HTTPException(status_code=400, detail="File is not an image (invalid content)")
        
        extracted_data = equalizer(contents)
        response = json.loads(extracted_data)
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))