# Data Extractor
This project focuses on extracting and organisig various data required for the system from media files like pdf and images


# Prerequisites
Python 3.11.7 installed.


## Installing Tessaract OCR:
### For Windows
Install the latest version of [tessaract OCR](https://github.com/UB-Mannheim/tesseract/wiki) into the C directory and add the path (C:\Program Files \Tesseract-OCR) to both System and User environment variables in Windows. 

### For Linux
For linux, run the following cmds in your terminal to ensure tesseract is installed successfully
```
sudo apt update
sudo apt install tesseract-ocr
```

## Environment Variables
For the project to function, you'll need to set up your .env file to have the following.
```
OPENAI_API_KEY = your_openai_api_key
MONGO_URI = Mongo db connection string
DB_NAME = database name
EXT_COLLECTION = extraction collection
```

## Running the Code.
1. Clone the repository or downlaod the zip file from GitHub

2. Open a Terminal and run the pip cmd to install all depedencies.

```
pip install -r requirements.txt
```

4. To run the application.  
```
 uvicorn main:app --reload
```

# Extra
A docker file is also present within the repo, for quicker installation, you can directly run the docker file present