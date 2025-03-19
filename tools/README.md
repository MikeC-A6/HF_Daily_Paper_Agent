# Tools Implementation Guide

This guide explains how to create and integrate new tools into the HF Daily Paper Agent system.

## Overview

The agent system uses function-based tools decorated with the `@function_tool` decorator from the OpenAI Agents SDK. These tools are implemented as async Python functions that agents can call to perform specific tasks.

## Creating a New Tool

### 1. Basic Tool Structure

Create a new Python file in the `tools/` directory (e.g., `tools/my_new_tool.py`):

```python
from typing import Dict, Any, Optional
from agents import function_tool  # Import the function_tool decorator

@function_tool
async def my_new_tool(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Description of what your tool does.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the second parameter (optional)
        
    Returns:
        A dictionary containing the result of the tool execution
    """
    # Tool implementation
    result = {}
    
    # Your logic here
    result["some_key"] = f"Processed {param1}"
    
    if param2:
        result["another_key"] = param2 * 2
    
    return result
```

### 2. Important Decorator Requirements

The `@function_tool` decorator automatically:

- Converts your function into a tool the agent can use
- Extracts parameter names, types, and docstrings to inform the agent about how to use the tool
- Creates a schema for the function's parameters and return type

For this to work properly:

- Use **type hints** for all parameters and return values
- Write a **detailed docstring** using Google-style or NumPy-style format
- Include **descriptions for all parameters** in the Args section
- Describe the **return value** in the Returns section

### 3. Best Practices

#### Async Implementation
All tools should be implemented as `async` functions to allow for concurrent execution and proper integration with the agent system.

#### Error Handling
Handle exceptions within your tool and return structured error information:

```python
try:
    # Your tool logic
    return {"success": True, "result": result}
except Exception as e:
    return {"success": False, "error": str(e)}
```

#### Typed Parameters
Use proper type hints to help the agent understand parameter types:

```python
from typing import Dict, List, Any, Optional, Union
```

#### Clear Documentation
Write clear documentation for your tool's parameters and return values to help the agent use it correctly.

## Example Tool Implementation

Here's a simple example based on the existing tools:

```python
"""
Tool for fetching information about a GitHub repository.
"""

import aiohttp
from typing import Dict, Any, Optional
from agents import function_tool

@function_tool
async def get_github_repo_info(repo_name: str, owner: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch information about a GitHub repository.
    
    Args:
        repo_name: The name of the repository
        owner: The owner of the repository (optional, defaults to using repo_name as owner/repo format)
        
    Returns:
        Dictionary containing repository information including:
        - full_name: The full name of the repository
        - description: Repository description
        - stars: Number of stars
        - forks: Number of forks
        - url: URL to the repository
    """
    try:
        # Parse owner/repo format if owner is not provided
        if not owner and "/" in repo_name:
            owner, repo_name = repo_name.split("/", 1)
        elif not owner:
            return {
                "success": False,
                "error": "Repository owner not provided and repo_name not in owner/repo format"
            }
        
        # Build the GitHub API URL
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        
        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status != 200:
                    return {
                        "success": False,
                        "error": f"GitHub API returned status code {response.status}"
                    }
                
                data = await response.json()
                
                # Extract and return the relevant information
                return {
                    "success": True,
                    "full_name": data.get("full_name"),
                    "description": data.get("description"),
                    "stars": data.get("stargazers_count"),
                    "forks": data.get("forks_count"),
                    "url": data.get("html_url")
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error fetching repository information: {str(e)}"
        }
```

## Integrating a Tool with an Agent

To use your new tool with an agent in `agent_code.py`, follow these steps:

### 1. Import the Tool

Import your tool at the top of `agent_code.py`:

```python
from tools.my_new_tool import my_new_tool
```

### 2. Add the Tool to an Agent

Add your tool to the agent's tools list:

```python
my_agent = Agent(
    name="MyAgent",
    instructions="You are an agent that can use various tools...",
    model="gpt-4o",
    tools=[my_new_tool, other_tool],  # Add your tool here
)
```

### 3. Update Agent Instructions

Update the agent's instructions to explain how to use the new tool:

```python
instructions=(
    "You are an agent that can perform various tasks. "
    "You have access to a tool called my_new_tool that can do X. "
    "When using my_new_tool, provide the following parameters: "
    "- param1: A string describing X "
    "- param2: (Optional) An integer representing Y "
)
```

## Real-World Examples

The system includes two function tools that you can use as reference:

1. `get_top_paper_pdf_url` in `tools/top_paper_getter.py`: 
   - Fetches the top paper from HuggingFace by upvotes
   - Handles API calls and error conditions
   - Uses helper functions for specific subtasks

2. `post_paper_to_slack` in `tools/slack_poster.py`:
   - Posts formatted paper summaries to Slack
   - Handles message formatting and API calls
   - Provides detailed error reporting 