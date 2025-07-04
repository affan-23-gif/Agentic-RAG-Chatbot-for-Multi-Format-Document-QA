# mcp.py
class MCPMessage:
    def __init__(self, sender: str, receiver: str, msg_type: str, trace_id: str, payload: dict):
        self.sender = sender
        self.receiver = receiver
        self.type = msg_type
        self.trace_id = trace_id
        self.payload = payload

    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "type": self.type,
            "trace_id": self.trace_id,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            sender=data.get("sender"),
            receiver=data.get("receiver"),
            msg_type=data.get("type"),
            trace_id=data.get("trace_id"),
            payload=data.get("payload")
        )

# Example Usage (for testing purposes)
if __name__ == "__main__":
    sample_payload = {
        "top_chunks": ["chunk1", "chunk2"],
        "query": "What are the KPIs?"
    }
    mcp_msg = MCPMessage(
        sender="RetrievalAgent",
        receiver="LLMResponseAgent",
        msg_type="CONTEXT_RESPONSE",
        trace_id="abc-123",
        payload=sample_payload
    )
    print(mcp_msg.to_dict())