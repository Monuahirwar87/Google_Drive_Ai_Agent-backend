from app.agent import agent

# Natural language question
user_query = "Find all invoice files"

# LangGraph agents expect a list of messages
response = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": user_query,
            }
        ]
    }
)

# Print the final assistant message
messages = response["messages"]

print("\nAssistant Response:\n")
print(messages[-1].content)