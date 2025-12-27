from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup_event():
    # Load existing PDFs from uploads folder
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    for filename in os.listdir("uploads"):
        if filename.endswith(".pdf"):
            try:
                path = os.path.join("uploads", filename)
                reader = PdfReader(path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                DOCUMENTS[filename] = text
                print(f"Loaded existing document: {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "is_admin": False})

@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "is_admin": True})

from pypdf import PdfReader
import google.generativeai as genai

# In-memory storage for simplicity
DOCUMENTS = {} 

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Parse PDF
        reader = PdfReader(file_location)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            
        DOCUMENTS[file.filename] = text
        return {"filename": file.filename, "status": "Processed", "text_preview": text[:100] + "..."}
    except Exception as e:
        return {"filename": file.filename, "status": "Error", "error": str(e)}

@app.get("/documents")
async def get_documents():
    return {"documents": list(DOCUMENTS.keys())}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    # Remove from memory
    if filename in DOCUMENTS:
        del DOCUMENTS[filename]
    
    # Remove from disk
    file_path = os.path.join("uploads", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"status": "Deleted", "filename": filename}
    
    return {"status": "Not Found", "filename": filename}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    query = data.get("query")
    
    if not DOCUMENTS:
        return {"answer": "No documents uploaded yet. Please upload a PDF first."}
    
    # Combine all docs for context (naive RAG)
    context = "\n\n".join([f"--- Document: {name} ---\n{text}" for name, text in DOCUMENTS.items()])
    
    try:
        # Check for API Key (Env or Request)
        api_key = data.get("api_key") or os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
             return {"answer": "⚠️ Missing Google Gemini API Key. \n\nPlease enter your API Key in the sidebar settings on the left, or set GEMINI_API_KEY env var."}

        genai.configure(api_key=api_key)
        
        # dynamic model selection with strict preference
        model_name = None
        available_models = []
        try:
             for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            print(f"Error listing models: {e}")

        # Priority list
        priorities = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-002',
            'models/gemini-1.5-flash-001',
            'models/gemini-1.5-pro',
            'models/gemini-1.0-pro',
            'models/gemini-pro'
        ]

        for p in priorities:
            if p in available_models:
                model_name = p
                break
        
        # Fallback if specific models not found (try loose match safely)
        if not model_name:
             for m_name in available_models:
                 if 'gemini-1.5-flash' in m_name:
                     model_name = m_name
                     break
        
        if not model_name and available_models:
            model_name = available_models[0]
            
        print(f"Available models: {available_models}")
        print(f"Selected model: {model_name}")
        
        if not model_name:
             return {"answer": "Error: No suitable Gemini models found for your API key."}

        model = genai.GenerativeModel(model_name)
        
        prompt = f"You are a helpful assistant. Answer the question based ONLY on the following documents:\n\n{context}\n\nQuestion: {query}"
        
        response = model.generate_content(prompt)
        return {"answer": response.text}
    except Exception as e:
        return {"answer": f"Error generating response: {str(e)}"}
