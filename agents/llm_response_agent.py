# agents/llm_response_agent.py
from mcp import MCPMessage
from openai import OpenAI # Or import from transformers for local models

class LLMResponseAgent:
    def __init__(self, coordinator_queue=None, openai_api_key: str = None):
        self.coordinator_queue = coordinator_queue
        # Initialize OpenAI client if using OpenAI API
        self.client = OpenAI(api_key=openai_api_key)
        # Or for local Hugging Face models:
        # from transformers import pipeline
        # self.llm_pipeline = pipeline("text-generation", model="distilgpt2") # Example

    def generate_response(self, retrieved_context: list[str], query: str):
        context_str = "\n".join(retrieved_context)
        prompt = f"Given the following context:\n\n{context_str}\n\nAnswer the following question: {query}\n\nIf the answer is not in the context, state that you don't have enough information."

        try:
            # Example with OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Or "gpt-4"
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content

            # Example with Hugging Face local model (uncomment and modify if using)
            # response = self.llm_pipeline(prompt, max_new_tokens=200, num_return_sequences=1)
            # return response[0]['generated_text']

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return "I apologize, but I encountered an error while generating the response."

    def handle_retrieval_result(self, mcp_message: MCPMessage):
        # This method is called by the Coordinator or RetrievalAgent to pass data
        if mcp_message.type == "RETRIEVAL_RESULT":
            payload = mcp_message.payload
            retrieved_context = payload["retrieved_context"]
            source_context_metadata = payload["source_context_metadata"]
            query = payload["query"]

            answer = self.generate_response(retrieved_context, query)

            if self.coordinator_queue:
                msg = MCPMessage(
                    sender="LLMResponseAgent",
                    receiver="UI", # Or back to Coordinator for UI display
                    msg_type="FINAL_ANSWER",
                    trace_id=mcp_message.trace_id,
                    payload={
                        "answer": answer,
                        "source_context": source_context_metadata,
                        "original_query": query
                    }
                )
                self.coordinator_queue.put(msg)
            return answer
        else:
            print(f"LLMResponseAgent received unsupported message type: {mcp_message.type}")