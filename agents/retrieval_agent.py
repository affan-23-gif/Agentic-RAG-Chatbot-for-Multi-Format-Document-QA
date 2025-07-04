# agents/retrieval_agent.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from mcp import MCPMessage

class RetrievalAgent:
    def __init__(self, embeddings_model_name: str = 'all-MiniLM-L6-v2', coordinator_queue=None):
        self.model = SentenceTransformer(embeddings_model_name)
        self.vector_store = None # This will be a FAISS index
        self.documents_metadata = [] # To store original chunks and their source info
        self.coordinator_queue = coordinator_queue

    def create_embeddings(self, texts: list[str]):
        return self.model.encode(texts).astype('float32')

    def add_documents(self, chunks: list[str], document_name: str, document_type: str, trace_id: str):
        if not chunks:
            print("No chunks to add.")
            return

        new_embeddings = self.create_embeddings(chunks)

        if self.vector_store is None:
            # Initialize FAISS index
            dimension = new_embeddings.shape[1]
            self.vector_store = faiss.IndexFlatL2(dimension)

        self.vector_store.add(new_embeddings)

        # Store metadata for retrieval and source context
        for i, chunk in enumerate(chunks):
            self.documents_metadata.append({
                "chunk": chunk,
                "document_name": document_name,
                "document_type": document_type,
                "chunk_id": len(self.documents_metadata) # Simple unique ID for each chunk
            })
        print(f"Added {len(chunks)} chunks to vector store.")

    def retrieve_relevant_chunks(self, query: str, k: int = 5):
        query_embedding = self.create_embeddings([query])
        if self.vector_store is None:
            print("Vector store is empty. No documents ingested yet.")
            return []

        # Perform similarity search
        distances, indices = self.vector_store.search(query_embedding, k)

        retrieved_chunks = []
        for idx in indices[0]:
            if idx < len(self.documents_metadata): # Ensure index is valid
                retrieved_chunks.append(self.documents_metadata[idx])
        return retrieved_chunks

    def handle_ingested_documents(self, mcp_message: MCPMessage):
        # This method is called by the Coordinator or IngestionAgent to pass data
        if mcp_message.type == "DOCUMENT_PARSED":
            payload = mcp_message.payload
            self.add_documents(
                chunks=payload["chunks"],
                document_name=payload["document_name"],
                document_type=payload["document_type"],
                trace_id=mcp_message.trace_id
            )
        else:
            print(f"RetrievalAgent received unsupported message type: {mcp_message.type}")

    def search_documents(self, query: str, trace_id: str):
        retrieved_items = self.retrieve_relevant_chunks(query)
        top_chunks_content = [item['chunk'] for item in retrieved_items]
        source_context = [
            f"Source: {item['document_name']}, Type: {item['document_type']}, Chunk ID: {item['chunk_id']}"
            for item in retrieved_items
        ]

        if self.coordinator_queue:
            msg = MCPMessage(
                sender="RetrievalAgent",
                receiver="LLMResponseAgent",
                msg_type="RETRIEVAL_RESULT",
                trace_id=trace_id,
                payload={
                    "retrieved_context": top_chunks_content,
                    "source_context_metadata": source_context,
                    "query": query
                }
            )
            self.coordinator_queue.put(msg)
        return retrieved_items