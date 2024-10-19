from fastapi import FastAPI
from pydantic import BaseModel
import stanza
import pandas as pd
from fastapi.responses import StreamingResponse
import io

app = FastAPI()
stanza.download('en')
nlp = stanza.Pipeline('en')

class TextRequest(BaseModel):
    text: str

@app.post("/process")
async def process_text(request: TextRequest):
    doc = nlp(request.text)
    entities = [{'text': ent.text, 'type': ent.type} for ent in doc.ents]
    
    # Create a DataFrame
    df = pd.DataFrame(entities)
    
    # Convert to CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return StreamingResponse(io.BytesIO(csv_buffer.getvalue().encode()), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=entities.csv"})