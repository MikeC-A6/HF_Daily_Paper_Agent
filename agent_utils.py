"""
Utility functions for working with OpenAI Assistants API and Slack integrations
"""

import os
import json
import openai
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

def load_and_validate_env() -> Dict[str, Any]:
    """
    Load environment variables and validate required ones are present.
    
    Returns:
        Dict with success flag and related information or error message.
    """
    load_dotenv()
    
    # Check for required environment variables
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    slack_api_token = os.environ.get("SLACK_API_TOKEN")
    slack_channel = os.environ.get("SLACK_CHANNEL", "#ai-papers-and-research")
    
    if not openai_api_key:
        return {
            "success": False,
            "error": "OPENAI_API_KEY is required but not found in environment variables"
        }
    
    if not slack_api_token:
        return {
            "success": False,
            "error": "SLACK_API_TOKEN is required but not found in environment variables"
        }
    
    return {
        "success": True,
        "openai_api_key": openai_api_key,
        "slack_api_token": slack_api_token,
        "slack_channel": slack_channel
    }

async def initialize_agent(instructions: str, name: str, tools: List[Any]) -> Any:
    """
    Initialize an OpenAI Assistant with the given instructions, name and tools.
    
    Args:
        instructions: The instructions for the agent
        name: The name of the agent
        tools: List of tools for the agent to use
    
    Returns:
        The initialized agent
    
    Raises:
        Exception: If environment validation fails or if initialization fails
    """
    # Validate environment
    env_result = load_and_validate_env()
    if not env_result["success"]:
        raise Exception(f"Failed to initialize agent: {env_result['error']}")
    
    # Set API key from validation
    api_key = env_result["openai_api_key"]
    
    try:
        # Create OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create assistant
        assistant = client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools,
            model="gpt-4-turbo-preview"  # Default model
        )
        
        return assistant
    except Exception as e:
        raise Exception(f"Failed to initialize agent: {str(e)}")

def check_slack_posting(result) -> Dict[str, Any]:
    """
    Check if an agent's run result includes a successful Slack post.
    
    Args:
        result: The result from the agent run
        
    Returns:
        Dict with success flag and related information
    """
    # Look for post_paper_to_slack tool call
    slack_post_tool_call = None
    slack_post_result = None
    
    # Find tool calls in the result
    for item in result.new_items:
        # Check if this is a tool call for post_paper_to_slack
        if isinstance(item, dict):
            if item.get("type") == "tool_use" and item.get("tool_use", {}).get("name") == "post_paper_to_slack":
                slack_post_tool_call = item
                break
        
    # If we found a tool call, look for the corresponding result
    if slack_post_tool_call:
        tool_call_id = slack_post_tool_call.get("id")
        for item in result.new_items:
            if isinstance(item, dict) and item.get("type") == "tool_result" and item.get("id") == f"{tool_call_id}_result":
                slack_post_result = item.get("tool_result", {})
                break
    
    if not slack_post_tool_call:
        return {
            "slack_post_successful": False,
            "error": "No post_paper_to_slack tool call found"
        }
    
    if not slack_post_result or not slack_post_result.get("success", False):
        return {
            "slack_post_successful": False,
            "error": slack_post_result.get("error", "Unknown error posting to Slack")
        }
    
    # Post was successful
    return {
        "slack_post_successful": True,
        "message_url": slack_post_result.get("message_url", ""),
        "channel": slack_post_result.get("channel", "")
    }

def format_handoff_data(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format paper data for handoff between agents.
    
    Args:
        paper_data: Dictionary containing paper information
        
    Returns:
        Dictionary formatted for handoff
    """
    return {
        "paper_title": paper_data.get("title", ""),
        "arxiv_id": paper_data.get("arxiv_id", ""),
        "upvotes": paper_data.get("upvotes", 0),
        "pdf_url": paper_data.get("pdf_url", ""),
        "additional_info": None
    } 