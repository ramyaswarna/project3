import openai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()

# Print the API key for debugging
print("🔑 OpenAI API Key Loaded:", os.getenv("OPENAI_API_KEY"))

# Set the API key in OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class ModelLoader:
    def __init__(self):
        self.model = "text-embedding-ada-002"

    def generate_embedding(self, text):
        """Generates embeddings using OpenAI"""
        try:
            response = openai.Embedding.create(
                model=self.model,
                input=text[:3000]
            )
            embedding = response["data"][0]["embedding"]
            if len(embedding) == 1536:
                return embedding
            else:
                print("Embedding has incorrect dimensions!")
                return None
        except Exception as e:
            print(f" OpenAI embedding error: {e}")
            return None

# Test if API key is detected
if __name__ == "__main__":
    model = ModelLoader()
    embedding = model.generate_embedding("Sample policy text")
    print("Generated Embedding:", embedding[:5] if embedding else "Failed to generate")
