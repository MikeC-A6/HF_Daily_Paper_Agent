import os
import asyncio
from agent_code import main as agent_main

def get_api_key():
    # First try to get from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # If not in environment, try to read from .env file
    if not api_key:
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        # Remove any quotes if present
                        api_key = api_key.strip("'\"")
                        break
        except Exception as e:
            print(f"Error reading .env file: {e}")
    
    return api_key

if __name__ == "__main__":
    # Get API key
    api_key = get_api_key()
    
    if not api_key or api_key == "your_api_key_here":
        print("Please set your OPENAI_API_KEY in the .env file before running.")
    else:
        # Set the API key in the environment for the agent to use
        os.environ["OPENAI_API_KEY"] = api_key
        # Run the agent
        asyncio.run(agent_main()) 