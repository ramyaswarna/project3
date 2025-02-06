from flask import Flask, request, jsonify
import pdfplumber  
from database import Database, get_database
import openai
import os
from dotenv import load_dotenv
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
db = Database()

def generate_answer_with_llm(query, chunks):
    if not chunks:
        return "No relevant information found in the database."

    # Combine chunks into a single context passage
    context = "\n\n".join([f"Chunk {i+1}: {chunk['content']}" for i, chunk in enumerate(chunks)])

    # Construct the prompt for OpenAI
    prompt = f"""
    You are an expert assistant helping answer user queries based on retrieved document text.
    Here is the retrieved context from the database:
    {context}

    Based on this, answer the following user query concisely and accurately:
    {query}
    """

    # try:
    #     response = openai.ChatCompletion.create(
    #         model="gpt-4o-mini", 
    #         messages=[{"role": "system", "content": "You are a helpful assistant."},
    #                   {"role": "user", "content": prompt}],
    #         max_tokens=300  
    #     )
    #     return response["choices"][0]["message"]["content"].strip()
    # except Exception as e:
    #     print(f" OpenAI API Error: {e}")
    #     return "Error generating response from AI."
    try:
        response = requests.post(
            "http://3.215.242.114/generate",
            headers={"Content-Type": "application/json"},
            json={"prompt": prompt}
        )

        if response.status_code == 200:
            return response.json().get("response", "Error: No response generated.")
        else:
            return f"Error: LLM API returned status {response.status_code}"
    
    except Exception as e:
        return f"Error contacting LLM API: {e}"

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    """API Endpoint to upload a PDF & store it in MongoDB"""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save the PDF temporarily
    pdf_path = f"/tmp/{file.filename}"
    file.save(pdf_path)

    # Extract text from PDF
    doc = pdfplumber.open(pdf_path)
    text_content = "\n".join([page.get_text() for page in doc])

    # Store extracted text in MongoDB using chunking
    db.store_vector(title=file.filename, content=text_content)

    return jsonify({"message": "PDF uploaded and stored in chunks"}), 200

# @app.route("/search", methods=["GET"])
# def search():
#     """API Endpoint to perform vector search and refine results with OpenAI"""
#     query = request.args.get("query")
#     if not query:
#         return jsonify({"error": "Query parameter is required"}), 400

#     # Retrieve relevant chunks from MongoDB
#     relevant_chunks = db.query_database(query)

#     if not relevant_chunks:
#         return jsonify({"message": "No matching results found"}), 200

#     # Use OpenAI GPT to generate a precise answer
#     refined_answer = generate_answer_with_llm(query, relevant_chunks)
#     print(f"**refined_answer** {refined_answer}")

#     return jsonify({
#         "query": query,
#         "ai_answer": refined_answer
#         # "retrieved_chunks": relevant_chunks  #
#     })
# @app.route("/search", methods=["GET","POST"])
# def search():
#     """API Endpoint to perform vector search and return both VectorDB and LLM response."""
#     query = request.args.get("query")
#     if not query:
#         return jsonify({"error": "Query parameter is required"}), 400

#     relevant_chunks = db.query_database(query)

#     if not relevant_chunks:
#         return jsonify({
#             "message": "No matching results found",
#             "vector_db_output": []
#         }), 200

#     refined_answer = generate_answer_with_llm(query, relevant_chunks)

#     return jsonify({
#         "query": query,
#         "ai_answer": refined_answer,
#         "vector_db_output": relevant_chunks  
#     })
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.args.get("query")

    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        db = get_database()  #  Create database connection inside the request
        collection = db["your_collection_name"]
        relevant_chunks = list(collection.find({"content": {"$regex": query, "$options": "i"}}))
        
        return jsonify({
            "query": query,
            "vector_db_output": relevant_chunks
        })
    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
