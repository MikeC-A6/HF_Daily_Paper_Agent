# Agent Workflow

This diagram illustrates the detailed workflow between agents, including the handoff process, data flow, and the sequence of operations.

```mermaid
sequenceDiagram
    participant User
    participant Main as main.py
    participant Orch as OrchestratorAgent<br>(o3-mini)
    participant TopPaper as get_top_paper_pdf_url
    participant Datasets as HuggingFace Datasets
    participant Summary as PaperSummaryAgent<br>(gpt-4o)
    participant WebSearch as WebSearchTool
    participant SlackPost as post_paper_to_slack
    participant Slack as Slack Workspace

    User->>Main: Run agent_main()
    Main->>Orch: Create & initialize
    Note over Orch: Instructions:<br>1. Get top paper<br>2. Hand off to summary agent
    
    Orch->>TopPaper: Call get_top_paper_pdf_url()
    TopPaper->>Datasets: Query top paper by upvotes
    Datasets-->>TopPaper: Return paper data
    TopPaper-->>Orch: Return paper details
    
    Note over Orch,Summary: Handoff Process
    
    Orch->>Summary: handoff() with PaperData model
    Note over Summary: PaperData contains:<br>- title<br>- arxiv_id<br>- upvotes<br>- pdf_url
    
    Note over Summary: Instructions:<br>1. Read paper PDF<br>2. Create summary<br>3. Post to Slack
    
    Summary->>WebSearch: Search for PDF URL
    WebSearch-->>Summary: Return paper content
    
    Summary->>Summary: Generate comprehensive summary
    
    Summary->>SlackPost: post_paper_to_slack()
    SlackPost->>Slack: Format & post message
    Slack-->>SlackPost: Return message URL
    SlackPost-->>Summary: Return posting result
    
    Summary-->>Main: Return final structured output
    Main-->>User: Display results & success status
```

The sequence diagram shows:
1. The user initiates the process
2. The main script creates the orchestrator agent
3. The orchestrator gets paper information and hands off to the summary agent
4. The summary agent retrieves and processes the paper
5. The summary agent posts to Slack
6. Results are returned to the user 