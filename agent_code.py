from agents import Agent, WebSearchTool, Runner, handoff, RunContextWrapper
from tools.top_paper_getter import get_top_paper_pdf_url  # Import the decorated function
from tools.slack_poster import post_paper_to_slack  # Import the Slack posting tool
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Default Slack channel for paper summaries (used as a constant)
PAPER_CHANNEL = "#ai-papers-and-research"

# Define a model for paper data that can be passed during handoff
class PaperData(BaseModel):
    title: str
    arxiv_id: str
    upvotes: int
    pdf_url: str
    additional_info: Optional[str] = None

# Define the structured output model for the PaperSummaryAgent
class PaperSummaryOutput(BaseModel):
    title: str = Field(description="The title of the paper")
    arxiv_id: str = Field(description="The arXiv ID of the paper")
    upvotes: int = Field(description="Number of upvotes the paper received")
    pdf_url: str = Field(description="URL to the paper's PDF")
    summary: str = Field(description="Comprehensive summary of the paper in plain language")

# Define the on_handoff callback function - required by the handoff() function
async def on_paper_handoff(ctx: RunContextWrapper, input_data: PaperData):
    print(f"Handing off to PaperSummaryAgent with paper: {input_data.title}")
    return

# Validate that the Slack API token is set
slack_token = os.environ.get("SLACK_API_TOKEN")
if not slack_token:
    print("WARNING: SLACK_API_TOKEN environment variable is not set. Slack posting will fail.")
else:
    print(f"Slack API token is configured (length: {len(slack_token)})")

# Agent: Creates comprehensive summaries from PDF URLs with enhanced instructions
paper_summary_agent = Agent(
    name="PaperSummaryAgent",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are an expert research summarization agent specialized in academic papers from arXiv. "
        "You will be given information about the top daily paper including its title, arxiv ID, upvotes, and PDF URL. "
        "Your task is to create a comprehensive summary and final report about this paper, and then share it to Slack. "
        "\n\n"
        "You MUST follow these steps in order:\n"
        "1. Use the web search tool to navigate to the provided PDF URL and read its contents\n"
        "2. Create a comprehensive summary of the paper\n"
        "3. Return the structured output with all the paper details and your summary\n"
        "4. IMPORTANT: Post this summary to Slack as your FINAL ACTION using the post_paper_to_slack tool\n"
        "\n"
        "When creating your summary:\n"
        "- Explain the paper's main research question or problem\n"
        "- Summarize the approach and methods used\n"
        "- Highlight key findings and important insights\n"
        "- Describe potential implications and applications\n"
        "- Use clear, straightforward language avoiding heavy technical jargon\n"
        "- Make complex concepts understandable to non-experts\n"
        "\n"
        f"For Step 4 (Posting to Slack), you MUST use the post_paper_to_slack tool with these parameters:\n"
        "- title: The paper title (exactly as provided to you)\n"
        "- arxiv_id: The arXiv ID (exactly as provided to you)\n"
        "- upvotes: The number of upvotes (exactly as provided to you)\n"
        "- pdf_url: The PDF URL (exactly as provided to you)\n"
        "- summary: Your comprehensive summary of the paper\n"
        f"- channel: \"{PAPER_CHANNEL}\" (always use this exact channel name)\n"
        "\n"
        "Step 4 MUST BE PERFORMED as your final action. After you have returned your structured output, "
        "EXPLICITLY STATE that you will now post to Slack and then call the post_paper_to_slack tool. "
        "This is a critical part of your task and must not be skipped.\n"
        "\n"
        "Your final structured output for step 3 should include:\n"
        "1. The paper title (exactly as provided)\n"
        "2. The arXiv ID (exactly as provided)\n"
        "3. The number of upvotes (exactly as provided)\n"
        "4. The PDF URL (exactly as provided)\n"
        "5. Your comprehensive summary of the paper\n"
        "\n"
        "Remember: After returning your structured output, your FINAL ACTION must always be to post to Slack."
    ),
    model="gpt-4o",
    tools=[WebSearchTool(), post_paper_to_slack],  # Add the Slack posting tool
    output_type=PaperSummaryOutput  # Add structured output type
)

# Create a handoff object with structured input
paper_summary_handoff = handoff(
    agent=paper_summary_agent,
    input_type=PaperData,
    on_handoff=on_paper_handoff,  # Add the required callback function
    tool_name_override="summarize_paper",
    tool_description_override="Hand off to PaperSummaryAgent with paper details to create a comprehensive summary"
)

# Orchestrator Agent: Gets paper info and hands off to summary agent
orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are an orchestrator agent that helps create summaries of top AI research papers. "
        "Your role is to: "
        "1. Use the get_top_paper_pdf_url tool to get the top daily paper by upvotes and its information including the PDF URL "
        "2. Once you have the paper information, hand off to the PaperSummaryAgent by using the summarize_paper tool. "
        "   When handing off, you MUST provide the following information in the exact format expected: "
        "   {\n"
        '     "title": "The full paper title",\n'
        '     "arxiv_id": "The arxiv ID of the paper",\n'
        '     "upvotes": The number of upvotes as integer,\n'
        '     "pdf_url": "The PDF URL for the paper"\n'
        "   }"
        "\n\n"
        "The PaperSummaryAgent will then create the final comprehensive report and post it to Slack. "
        "Do not attempt to create your own summary - your job is only to fetch the paper information and hand off to the specialist agent."
    ),
    model="o3-mini",
    tools=[get_top_paper_pdf_url],  # Only need the paper info tool
    handoffs=[paper_summary_handoff]  # Add the handoff object to the agent
)

def check_slack_posting(result) -> Dict[str, Any]:
    """
    Check if the agent successfully used the Slack posting tool.
    
    Args:
        result: The result from Runner.run
        
    Returns:
        Dict with slack_posted (bool) and details
    """
    slack_posted = False
    slack_result = None
    
    # Check in the new items for any tool calls to post_paper_to_slack
    for item in result.new_items:
        # Check if this is a tool call
        if hasattr(item, 'tool') and hasattr(item, 'raw') and item.tool == 'post_paper_to_slack':
            slack_posted = True
            slack_result = item.raw
            break
    
    return {
        "slack_posted": slack_posted,
        "slack_result": slack_result,
        "slack_url": slack_result.get("message_url") if slack_result and isinstance(slack_result, dict) else None
    }

async def main():
    print("Starting paper summary agent...")
    print(f"Using Slack channel: {PAPER_CHANNEL}")
    
    # Run the agent
    result = await Runner.run(
        orchestrator_agent, 
        "Please provide a summary of today's top AI research paper."
    )
    
    # Check if Slack posting was successful
    slack_info = check_slack_posting(result)
    
    # Print the final output
    print("\n" + "="*80)
    print(f"Slack posting: {'✅ SUCCESSFUL' if slack_info['slack_posted'] else '❌ FAILED'}")
    if slack_info['slack_url']:
        print(f"Slack message URL: {slack_info['slack_url']}")
    print("="*80 + "\n")
    
    print(result.final_output)

# Run the orchestration process
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
