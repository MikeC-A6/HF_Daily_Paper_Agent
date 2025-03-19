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

The system consists of three main components:
- `get_top_paper_pdf_url`: A tool that fetches the top paper's details including PDF URL
- `PaperSummaryAgent`: Generates a comprehensive summary from the PDF
- `post_paper_to_slack`: A tool that formats and posts the summary to a Slack channel

An orchestrator agent coordinates these components to produce the final report and share it on Slack.

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
python agent_code.py
```

The agent will:
1. Find the top daily paper on HuggingFace by upvotes
2. Extract the paper's PDF URL
3. Create a comprehensive summary of the paper
4. Post the formatted summary to Slack
5. Output a complete report with all relevant information

## Development

### Key Files
- `agent_code.py`: Main agent orchestration code
- `tools/top_paper_getter.py`: Tool to fetch the top paper's details
- `tools/slack_poster.py`: Tool to post paper summaries to Slack
- `requirements.txt`: Project dependencies 