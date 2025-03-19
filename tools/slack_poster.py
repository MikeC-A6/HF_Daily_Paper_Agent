"""
Tool for posting paper summaries to Slack.
Formats structured paper summary output and posts to a Slack channel.
"""

import os
import re
from typing import Dict, Any, Optional
from datetime import datetime
from agents import function_tool
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default Slack channel for paper summaries (used internally, not as a default parameter)
DEFAULT_CHANNEL = "#ai-papers-and-research"

# Validate Slack token on module load for better debugging
_slack_token = os.environ.get("SLACK_API_TOKEN")
if not _slack_token:
    print("WARNING: SLACK_API_TOKEN environment variable is not set in slack_poster.py")

@function_tool
async def post_paper_to_slack(
    title: str,
    arxiv_id: str,
    upvotes: int,
    pdf_url: str,
    summary: str,
    channel: str
) -> Dict[str, Any]:
    """
    Format a paper summary and post it to a Slack channel.
    
    Args:
        title: The title of the paper
        arxiv_id: The arXiv ID of the paper
        upvotes: Number of upvotes the paper received
        pdf_url: URL to the paper's PDF
        summary: Comprehensive summary of the paper
        channel: Slack channel to post to (e.g., #ai-papers-and-research)
        
    Returns:
        Dictionary with status of the posting operation and message URL if successful
    """
    # Use the default channel if none is provided
    if not channel:
        channel = DEFAULT_CHANNEL
        
    # Force reload environment variables
    load_dotenv()
    
    # Get the Slack API token from environment variables
    slack_token = os.environ.get("SLACK_API_TOKEN")
    if not slack_token:
        error_msg = "SLACK_API_TOKEN environment variable not set"
        print(f"ERROR: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    
    try:
        # Initialize Slack client
        client = WebClient(token=slack_token)
        
        # Format the message as Markdown blocks for Slack
        blocks = _format_paper_blocks({
            "title": title,
            "arxiv_id": arxiv_id,
            "upvotes": upvotes,
            "pdf_url": pdf_url,
            "summary": summary,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        # Post the message to Slack
        response = client.chat_postMessage(
            channel=channel,
            blocks=blocks,
            text=f"New research paper: {title}"  # Fallback text
        )
        
        # Print success information for debugging
        print(f"Successfully posted paper summary to Slack channel: {channel}")
        message_url = f"https://slack.com/archives/{response['channel']}/p{response['ts'].replace('.', '')}"
        print(f"Message URL: {message_url}")
        
        # Return success information
        return {
            "success": True,
            "channel": channel,
            "message_ts": response["ts"],
            "message_url": message_url
        }
        
    except SlackApiError as e:
        error_msg = f"Error posting to Slack: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

def _truncate_text(text: str, max_length: int) -> str:
    """Truncate text to ensure it doesn't exceed Slack's character limits."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def _format_markdown_for_slack(text: str) -> str:
    """
    Format markdown text to be compatible with Slack's mrkdwn format.
    
    Args:
        text: Markdown text to format
        
    Returns:
        Slack mrkdwn formatted text
    """
    # First, ensure consistent line breaks (sometimes paragraphs might have single line breaks)
    text = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', text)
    
    # Process the text line by line for better control
    lines = text.split('\n')
    formatted_lines = []
    
    # Track if we're in a list context to handle nested lists
    in_list = False
    list_indent = 0
    prev_was_empty = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip multiple consecutive empty lines
        if not line.strip():
            if not prev_was_empty:
                formatted_lines.append("")
                prev_was_empty = True
            i += 1
            continue
        
        prev_was_empty = False
        
        # Handle section titles - convert to Slack-specific formatting
        if line.strip() and not line.strip().startswith(('#', '*', '-', '+', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            # Check if the line appears to be a section title (all caps, ends with :, etc.)
            if line.strip().endswith(':') and len(line.strip()) < 50:
                # Format as a section title (bold)
                line = f"*{line.strip()}*"
                formatted_lines.append(line)
                # Add empty line after section title if the next line isn't already empty
                if i+1 < len(lines) and lines[i+1].strip():
                    formatted_lines.append("")
                i += 1
                continue
        
        # Handle headers - Slack uses * for bold
        if re.match(r'^# ', line):
            # H1: Convert to bold with additional emphasis
            title_text = line[2:].strip()
            # Remove trailing colons if present in headers
            if title_text.endswith(':'):
                title_text = title_text[:-1]
            formatted_lines.append(f"*{title_text}*")
            # Add empty line after header if the next line isn't already empty
            if i+1 < len(lines) and lines[i+1].strip():
                formatted_lines.append("")
        elif re.match(r'^## ', line):
            # H2: Convert to bold
            title_text = line[3:].strip()
            # Remove trailing colons if present in headers
            if title_text.endswith(':'):
                title_text = title_text[:-1]
            formatted_lines.append(f"*{title_text}*")
            # Add empty line after header if the next line isn't already empty
            if i+1 < len(lines) and lines[i+1].strip():
                formatted_lines.append("")
        elif re.match(r'^### ', line):
            # H3: Convert to bold with bullet
            title_text = line[4:].strip()
            # Remove trailing colons if present in headers
            if title_text.endswith(':'):
                title_text = title_text[:-1]
            formatted_lines.append(f"• *{title_text}*")
            # Add empty line after header if the next line isn't already empty
            if i+1 < len(lines) and lines[i+1].strip():
                formatted_lines.append("")
        # Handle bullet points - Slack uses • or -
        elif re.match(r'^\s*[\*\-\+] ', line):
            # Extract the indentation level
            indent = len(line) - len(line.lstrip())
            marker_match = re.match(r'^\s*([\*\-\+])\s', line)
            if marker_match:
                # Get the content after the bullet marker
                content = re.sub(r'^\s*[\*\-\+]\s', '', line)
                
                # Check if there's a bold section with a colon
                content = re.sub(r'\*\*(.*?):\*\*', r'*\1:*', content)
                
                # Process bold/italic in the content
                content = _process_inline_formatting(content)
                
                # Replace the marker with Slack's bullet and preserve indentation
                bullet = "•"
                
                # Add appropriate indentation
                if indent > list_indent:
                    # Increased indentation
                    bullet = "   " + bullet
                elif indent < list_indent and indent > 0:
                    # Decreased indentation but still nested
                    bullet = " " + bullet
                
                formatted_lines.append(f"{bullet} {content}")
                in_list = True
                list_indent = indent
            else:
                # Process inline formatting for any text
                line = _process_inline_formatting(line)
                formatted_lines.append(line)
        # Handle numbered lists - Slack needs numbers with a period and space
        elif re.match(r'^\s*\d+\.\s', line):
            # Get the content after the number
            content = re.sub(r'^\s*\d+\.\s', '', line)
            
            # Check if there's a bold section with a colon
            content = re.sub(r'\*\*(.*?):\*\*', r'*\1:*', content)
            
            # Process bold/italic in the content
            content = _process_inline_formatting(content)
            
            # Keep the numbered list as is, Slack supports it
            # Make sure there's a space after the period
            num_match = re.match(r'^\s*(\d+)\.', line)
            if num_match:
                num = num_match.group(1)
                # Extract the indentation
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                formatted_lines.append(f"{indent_str}{num}. {content}")
            else:
                # Process inline formatting for any text
                line = _process_inline_formatting(line)
                formatted_lines.append(line)
            in_list = True
        # Handle code blocks
        elif line.startswith('```'):
            # Slack uses ``` for code blocks just like markdown
            formatted_lines.append(line)
        elif line.startswith('`') and line.endswith('`') and len(line) > 2:
            # Inline code - Slack uses ` just like markdown
            formatted_lines.append(line)
        # Handle other lines
        else:
            # Check if there's a bold section with a colon
            line = re.sub(r'\*\*(.*?):\*\*', r'*\1:*', line)
            
            # Process inline formatting
            line = _process_inline_formatting(line)
            
            # If we were in a list but this line isn't a list item, add a line break
            if in_list and not (re.match(r'^\s*[\*\-\+] ', line) or re.match(r'^\s*\d+\.\s', line)):
                if line.strip():  # Only if the line is not empty
                    in_list = False
                    if not formatted_lines[-1] == "":  # Only add if the last line wasn't already empty
                        formatted_lines.append("")  # Add an empty line after list
            
            formatted_lines.append(line)
        
        i += 1
    
    # Join the lines back together
    result = '\n'.join(formatted_lines)
    
    # Clean up any excessive line breaks (more than 2 consecutive newlines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result

def _process_inline_formatting(text: str) -> str:
    """
    Process inline formatting like bold and italic for Slack.
    
    Args:
        text: Text to process
        
    Returns:
        Text with proper Slack formatting
    """
    # Handle specific patterns like "**Key:**" -> "*Key:*"
    text = re.sub(r'\*\*([\w\s]+):\*\*', r'*\1:*', text)
    
    # Bold: Replace ** with * (Slack uses single asterisks for bold)
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    
    # Replace __text__ with _text_ (for italic)
    text = re.sub(r'__(.*?)__', r'_\1_', text)
    
    return text

def _format_paper_blocks(paper: Dict[str, Any]) -> list:
    """
    Format a paper as Slack blocks.
    
    Args:
        paper: Paper dictionary with title, arxiv_id, upvotes, pdf_url, summary, and date
        
    Returns:
        List of Slack blocks for the paper.
    """
    blocks = [
        # Header with the paper title
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": _truncate_text(paper.get("title", "Unknown title"), 150),
                "emoji": True
            }
        },
        # Divider
        {"type": "divider"},
        # Paper metadata
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Date:*\n{paper.get('date', 'Unknown')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*arXiv ID:*\n<https://arxiv.org/abs/{paper.get('arxiv_id')}|{paper.get('arxiv_id')}>"
                }
            ]
        },
        # Upvotes and PDF Link
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Upvotes:* {paper.get('upvotes', 0)} {'🔥' if paper.get('upvotes', 0) > 5 else ''}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*<{paper.get('pdf_url', '')}|View the full paper PDF>*"
                }
            ]
        },
        # Divider before summary
        {"type": "divider"},
        # Summary header
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*AI-Generated Summary:*"
            }
        }
    ]
    
    # Get the summary and format it for Slack
    summary = paper.get("summary", "No summary available.")
    
    # Format the markdown for Slack
    formatted_summary = _format_markdown_for_slack(summary)
    
    # Split the summary into chunks of ~1900 characters (Slack block limit is 2000)
    max_chars = 1900
    start = 0
    
    while start < len(formatted_summary):
        # Find a good breaking point
        end = start + max_chars
        
        if end < len(formatted_summary):
            # Try to find a paragraph break
            paragraph_break = formatted_summary.rfind('\n\n', start, end)
            if paragraph_break > start:
                end = paragraph_break + 2  # Include the newlines
            else:
                # Try to find a newline
                newline = formatted_summary.rfind('\n', start, end)
                if newline > start:
                    end = newline + 1  # Include the newline
                else:
                    # Try to find a space
                    space = formatted_summary.rfind(' ', start, end)
                    if space > start:
                        end = space + 1  # Include the space
        
        # Extract the chunk
        chunk = formatted_summary[start:end]
        
        # Add the chunk as a block
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": _truncate_text(chunk, 1950)
            }
        })
        
        start = end
    
    # Add a context block at the end with a link to arXiv
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"<https://arxiv.org/abs/{paper.get('arxiv_id')}|View on arXiv> • Generated by AI Paper Agent"
            }
        ]
    })
    
    return blocks

# Test the function when running as a script
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Load environment variables again to be sure
        load_dotenv()
        
        # Check if the Slack token is set
        slack_token = os.environ.get("SLACK_API_TOKEN")
        if not slack_token:
            print("ERROR: SLACK_API_TOKEN environment variable not set")
            return
        
        print(f"Slack token found (length: {len(slack_token)})")
        
        # Test with a summary that includes various markdown elements
        test_summary = """
This is a test summary of a paper about transformers.

# Key Findings

* Transformers are **efficient** and scalable
* Self-attention is **powerful** for capturing relationships
  * Attention mechanisms allow for **parallelization**
  * They can capture **long-range dependencies**

## Methodology and Approach

1. Data preparation with **extensive preprocessing**
2. Model training using **gradient descent**
   1. Initial training with **learning rate scheduling**
   2. Fine-tuning on **domain-specific data**
3. Evaluation using **standard benchmarks**

### Results and Analysis:

The results show **significant improvements** over baseline models, with a **23% increase** in accuracy.

Key Innovations:

* **Dynamic State Evolution:** Improves model efficiency
* **Expressive Representation:** Enhances generalization capabilities
* **Scalable Architecture:** Allows for larger training datasets

In conclusion, this work represents a **major advancement** in the field of transformer models.
        """
        
        result = await post_paper_to_slack(
            title="Test Paper Title: Understanding Transformer Architectures",
            arxiv_id="2304.12345",
            upvotes=42,
            pdf_url="https://arxiv.org/pdf/2304.12345",
            summary=test_summary,
            channel="#ai-papers-and-research"
        )
        print(f"Result: {result}")
    
    asyncio.run(main()) 