# HF Daily Paper Agent

An AI agent system that finds and summarizes the top daily AI research papers from HuggingFace.

## Overview

This agent system uses the OpenAI Agents SDK to:
1. Automatically fetch the top daily paper from HuggingFace by upvotes
2. Retrieve the paper's PDF URL directly
3. Generate a comprehensive plain-language summary of the paper
4. Post the formatted summary to a Slack channel
5. Output a complete report with key information and the summary

## Architecture

The system is built using an agent-based architecture with OpenAI's Agent SDK and implements a handoff pattern:

### Components:
- **Orchestrator Agent (`OrchestratorAgent`)**: The lightweight coordinator that initiates the process, fetches the top paper data, and hands off to the summary agent
- **Paper Summary Agent (`PaperSummaryAgent`)**: The specialized agent that creates comprehensive paper summaries and posts to Slack
- **Data Model (`PaperData`)**: A structured model for passing paper information during handoff between agents

### Tools:
- `get_top_paper_pdf_url`: A function tool that fetches the top paper details from HuggingFace datasets
- `post_paper_to_slack`: A function tool that formats and posts the summary to a Slack channel
- `WebSearchTool`: Used by the summary agent to read the paper contents

### Flow:
1. The orchestrator agent fetches the top paper details using the `get_top_paper_pdf_url` tool
2. It hands off the paper details to the paper summary agent using the OpenAI handoff pattern
3. The paper summary agent creates a comprehensive summary of the paper
4. The paper summary agent posts the formatted summary to Slack as its final action
5. The system outputs a complete report and verification of the Slack posting

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your API keys:
   - Create a `.env` file in the root directory
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`
   - Add your Slack Bot Token: `SLACK_API_TOKEN=xoxb-your-slack-bot-token-here`
   - Optionally, specify a custom Slack channel: `SLACK_CHANNEL=#your-channel-name`

## Slack Integration

The agent uses the Slack API to post paper summaries to a designated Slack channel:

1. Create a Slack app in your workspace with the following permissions:
   - `chat:write`
   - `chat:write.public`

2. Install the app to your workspace and get the Bot Token

3. Add the token to your `.env` file as `SLACK_API_TOKEN`

4. By default, summaries are posted to the `#ai-papers-and-research` channel, which you should create in your Slack workspace

## Usage

Run the agent with:
```
python main.py
```

The agent will:
1. Find the top daily paper on HuggingFace by upvotes
2. Extract the paper's PDF URL
3. Create a comprehensive summary of the paper
4. Post the formatted summary to Slack
5. Output a complete report with all relevant information

## Testing

The project includes unit tests for verifying different components:

1. Run all tests:
   ```
   python -m pytest tests/unit
   ```

2. Run specific test files:
   ```
   python -m pytest tests/unit/test_top_paper_getter.py
   python -m pytest tests/unit/test_agent_utils.py
   python -m pytest tests/unit/test_slack_poster.py
   ```

3. Run tests with verbose output:
   ```
   python -m pytest tests/unit -v
   ```

### Test Coverage:

- **top_paper_getter**: Tests for fetching top papers from HuggingFace datasets
- **agent_utils**: Tests for utility functions for environment setup, agent initialization, and result processing
- **slack_poster**: Tests for formatting and posting summaries to Slack

## Development

### Project Structure

```
HF_Daily_Paper_Agent/
├── agent_code.py        # Main agent orchestration code
├── agent_utils.py       # Utility functions for agents and environment
├── main.py              # Entry point wrapper
├── requirements.txt     # Project dependencies
├── tools/               # Function tools
│   ├── slack_poster.py  # Tool for posting to Slack
│   └── top_paper_getter.py # Tool for fetching top papers
├── tests/               # Test suite
│   └── unit/            # Unit tests
│       ├── test_agent_utils.py     # Tests for agent utilities
│       ├── test_slack_poster.py    # Tests for Slack posting
│       └── test_top_paper_getter.py # Tests for paper fetching
```

### Key Implementation Details

- **OpenAI Agents SDK**: Uses the latest SDK for creating and orchestrating agents
- **Handoff Pattern**: Implements the efficient handoff pattern between agents
- **Markdown Formatting**: Includes sophisticated Markdown-to-Slack formatting
- **Error Handling**: Robust error handling for dataset and API failures 