from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
import pandas as pd
from fastapi.responses import StreamingResponse
import io
from chromadb import HttpClient  # Importing HttpClient
import json
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from typing import List
import PyPDF2
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chroma client setup
chroma_client = HttpClient(host="localhost", port=8000)  # Adjust host and port as needed

# Get or create collection
collection_name = "my_collection"
try:
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "My first collection"}
    )
except Exception as e:
    logging.error(f"Error getting or creating collection: {str(e)}")
    raise HTTPException(status_code=500, detail="Failed to initialize collection")

# API setup
genai.configure(api_key='AIzaSyC_URviN9hww3tofDRVt6CbfdghlqfwCvE')

# Model setup
model = genai.GenerativeModel('gemini-pro')

class TextRequest(BaseModel):
    text: str

def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        logging.error(f"Error reading PDF file: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid PDF file")

@app.post("/add_documents")
async def add_documents(files: List[UploadFile] = File(...)):
    try:
        logging.info(f"Received {len(files)} files for upload.")
        for file in files:
            content = await file.read()
            text = extract_text_from_pdf(io.BytesIO(content))
            collection.add(
                documents=[text],
                metadatas=[{"filename": file.filename}],
                ids=[file.filename]
            )
        return {"message": f"{len(files)} documents added successfully"}
    except Exception as e:
        logging.error(f"Error adding documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/process")
async def process_text(request: TextRequest):
    prompt = f"Translate the following natural language request into a Chroma metadata query structure: '{request.text}'. The output should be a JSON object with key-value pairs representing metadata fields and their values or conditions."
    
    completion = model.generate_content(prompt)

    try:
        metadata_query = json.loads(completion.text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Failed to generate valid metadata query")

    results = collection.query(
        query_texts=[request.text],
        where=metadata_query,
        n_results=10
    )

    processed_results = []
    for i, doc in enumerate(results['documents'][0]):
        processed_results.append({
            'document': doc[:500],  # Truncate document content for CSV
            'metadata': json.dumps(results['metadatas'][0][i]),
            'distance': results['distances'][0][i]
        })

    df = pd.DataFrame(processed_results)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=query_results.csv"}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
