from typing import Dict, Any, List
from .vector_store import VectorStoreManager

class RAGManager:
    def __init__(self):
        """Initialize the RAG manager with vector store."""
        self.vector_store = VectorStoreManager()
    
    def get_relevant_context(self, 
                           framework: str,
                           test_steps: str,
                           html_content: str) -> str:
        """Get relevant context from similar test scripts."""
        similar_tests = self.vector_store.get_similar_tests(
            framework=framework,
            test_steps=test_steps,
            html_content=html_content
        )
        
        if not similar_tests:
            return ""
        
        # Format context from similar tests
        context = "Here are some similar test scripts and their outcomes:\n\n"
        
        for i, test in enumerate(similar_tests, 1):
            context += f"Similar Test {i}:\n"
            context += f"Success: {test['metadata']['success']}\n"
            error_msg = test['metadata'].get('error_message')
            if error_msg:
                context += f"Error: {error_msg}\n"
            context += f"Script:\n{test['document']}\n\n"
        
        return context
    
    def store_test_result(self,
                         framework: str,
                         test_script: str,
                         test_steps: str,
                         html_content: str,
                         success: bool,
                         error_message: str = None,
                         metadata: Dict[str, Any] = None):
        """Store a test result in the vector store."""
        self.vector_store.add_test_script(
            framework=framework,
            test_script=test_script,
            test_steps=test_steps,
            html_content=html_content,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    def enhance_prompt(self,
                      framework: str,
                      test_steps: str,
                      html_content: str,
                      base_prompt: str) -> str:
        """Enhance the base prompt with relevant context from similar tests."""
        context = self.get_relevant_context(
            framework=framework,
            test_steps=test_steps,
            html_content=html_content
        )
        
        if not context:
            return base_prompt
        
        # Determine if this is a multi-page test
        is_multi_page = isinstance(html_content, list) and len(html_content) > 1
        
        # Add context to the prompt without repeating guidelines
        enhanced_prompt = f"""
        {base_prompt}
        
        Here are some similar test scripts and their outcomes to help guide the generation:
        
        {context}
        
        IMPORTANT: Study the examples above carefully, especially noting:
        - Which selectors worked reliably
        - How page transitions were handled
        - What patterns to avoid (from failed examples)
        """
        
        if is_multi_page:
            enhanced_prompt += """
            Since this is a multi-page test, pay special attention to:
            - How navigation between pages was implemented in successful examples
            - The selectors used for each specific page context
            """
        
        return enhanced_prompt 