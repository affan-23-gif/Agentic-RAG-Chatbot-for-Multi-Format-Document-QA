# agents/coordinator_agent.py
import queue
import uuid
from mcp import MCPMessage
from agents.ingestion_agent import IngestionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.llm_response_agent import LLMResponseAgent

class CoordinatorAgent:
    def __init__(self, openai_api_key: str = None):
        self.message_queue = queue.Queue() # Central queue for MCP messages
        self.ingestion_agent = IngestionAgent(coordinator_queue=self.message_queue)
        self.retrieval_agent = RetrievalAgent(coordinator_queue=self.message_queue)
        self.llm_response_agent = LLMResponseAgent(coordinator_queue=self.message_queue, openai_api_key=openai_api_key)
        self.chat_history = [] # To manage multi-turn conversations (optional for basic impl)

    def handle_user_upload(self, file_path: str):
        trace_id = str(uuid.uuid4())
        print(f"Coordinator: Received upload request for {file_path} with trace_id: {trace_id}")
        # Simulate sending a message to IngestionAgent
        # In a real async system, this would be put on a queue for IngestionAgent to pick up
        self.ingestion_agent.process_document(file_path, trace_id)
        print("Coordinator: Document processing initiated by IngestionAgent.")

        # Process messages from the queue until a final answer or no more messages
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            print(f"Coordinator: Processing message from {msg.sender} to {msg.receiver} (Type: {msg.type}, Trace ID: {msg.trace_id})")
            if msg.type == "DOCUMENT_PARSED":
                self.retrieval_agent.handle_ingested_documents(msg)
            elif msg.type == "RETRIEVAL_RESULT":
                self.llm_response_agent.handle_retrieval_result(msg)
            elif msg.type == "FINAL_ANSWER":
                return msg.payload # Return answer to UI
        return {"answer": "No response generated.", "source_context": []}


    def handle_user_query(self, query: str):
        trace_id = str(uuid.uuid4())
        print(f"Coordinator: Received query '{query}' with trace_id: {trace_id}")

        # 1. Trigger RetrievalAgent to search
        self.retrieval_agent.search_documents(query, trace_id)

        # 2. Process messages from the queue (synchronously for this example)
        # In a more complex system, this would be an event loop or async processing
        final_answer_payload = None
        while not self.message_queue.empty():
            msg = self.message_queue.get()
            print(f"Coordinator: Processing message from {msg.sender} to {msg.receiver} (Type: {msg.type}, Trace ID: {msg.trace_id})")

            if msg.type == "RETRIEVAL_RESULT":
                # Pass the retrieval result to the LLMResponseAgent
                self.llm_response_agent.handle_retrieval_result(msg)
            elif msg.type == "FINAL_ANSWER":
                final_answer_payload = msg.payload
                break # Got the final answer

        if final_answer_payload:
            print(f"Coordinator: Final answer received for trace_id {trace_id}")
            return final_answer_payload
        else:
            return {"answer": "I couldn't find an answer based on the available documents.", "source_context": []}