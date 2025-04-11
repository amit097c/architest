from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
from .utils import extract_relevant_selectors

# Load environment variables
load_dotenv()

class VectorStoreManager:
    def __init__(self, persist_directory: str = "chroma_db"):
        """Initialize the vector store manager with ChromaDB."""
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use Azure OpenAI's embedding function
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-3-small",
            api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),  # Azure OpenAI endpoint
            api_type="azure",
            api_version="2023-05-15",
            deployment_id=os.getenv("OPENAI_API_DEPLOYMENT")
        )
        
        # Create or get collections for different frameworks
        self.playwright_collection = self.client.get_or_create_collection(
            name="playwright_tests",
            embedding_function=self.embedding_function
        )
        self.selenium_collection = self.client.get_or_create_collection(
            name="selenium_tests",
            embedding_function=self.embedding_function
        )
    
    def add_test_script(self, 
                       framework: str,
                       test_script: str,
                       test_steps: str,
                       html_content: str,
                       success: bool,
                       error_message: str = None,
                       metadata: Dict[str, Any] = None):
        """Add a test script to the vector store."""
        collection = self.playwright_collection if framework == "playwright" else self.selenium_collection
        
        # Create a unique ID for the document
        doc_id = f"{framework}_{len(collection.get()['ids'])}"
        
        # Handle multi-page content
        if isinstance(html_content, list):
            page_selectors = []
            for i, page_html in enumerate(html_content, 1):
                selectors = extract_relevant_selectors(page_html)
                page_selectors.append(f"Page {i}:\n{selectors}")
            relevant_selectors = "\n\n".join(page_selectors)
        else:
            relevant_selectors = extract_relevant_selectors(html_content)
        
        # Prepare the document text with enhanced context
        doc_text = f"""
        Test Steps:
        {test_steps}
        
        Page Structure:
        {relevant_selectors}
        
        Generated Script:
        {test_script}
        
        Success: {success}
        """
        if error_message:
            doc_text += f"\nError Message: {error_message}"
        
        # Add metadata with enhanced context
        if metadata is None:
            metadata = {}
        metadata.update({
            "framework": framework,
            "success": success,
            "num_pages": len(html_content) if isinstance(html_content, list) else 1,
            "has_dynamic_content": "wait_for_selector" in test_script or "wait_for_timeout" in test_script,
            "has_page_transitions": "goto" in test_script or "click" in test_script
        })
        if error_message:
            metadata["error_message"] = error_message
        
        # Add to collection
        collection.add(
            documents=[doc_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
    
    def get_similar_tests(self, 
                         framework: str,
                         test_steps: str,
                         html_content: str,
                         n_results: int = 3) -> List[Dict[str, Any]]:
        """Retrieve similar test scripts based on test steps and HTML content."""
        collection = self.playwright_collection if framework == "playwright" else self.selenium_collection
        
        # Handle multi-page content in query
        if isinstance(html_content, list):
            page_selectors = []
            for i, page_html in enumerate(html_content, 1):
                selectors = extract_relevant_selectors(page_html)
                page_selectors.append(f"Page {i}:\n{selectors}")
            relevant_selectors = "\n\n".join(page_selectors)
        else:
            relevant_selectors = extract_relevant_selectors(html_content)
        
        # Create query text with page flow information
        query_text = f"""
        Test Steps:
        {test_steps}
        
        Page Structure:
        {relevant_selectors}
        """
        
        # Query the collection
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results 