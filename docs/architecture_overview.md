# Architecture Overview

This diagram illustrates the overall architecture of the HF Daily Paper Agent system, showing the main components and their relationships.

```mermaid
graph TB
    subgraph "HF Daily Paper Agent"
        direction TB
        
        MainProcess["Main Process<br>(main.py)"]
        
        subgraph "Agent System"
            OAgent["Orchestrator Agent<br>(o3-mini model)"]
            PAgent["Paper Summary Agent<br>(gpt-4o model)"]
            
            OAgent --> |handoff| PAgent
        end
        
        subgraph "Tools"
            TPG["get_top_paper_pdf_url<br>(HuggingFace API)"]
            SPT["post_paper_to_slack<br>(Slack API)"]
            WST["WebSearchTool<br>(Paper Retrieval)"]
        end
        
        subgraph "External Services"
            HF["HuggingFace<br>Paper Datasets"]
            Slack["Slack<br>Workspace"]
        end
        
        MainProcess --> OAgent
        OAgent --> TPG
        PAgent --> WST
        PAgent --> SPT
        TPG --> HF
        SPT --> Slack
    end
    
    style MainProcess fill:#f9f,stroke:#333,stroke-width:2px
    style OAgent fill:#bbf,stroke:#333,stroke-width:2px
    style PAgent fill:#bbf,stroke:#333,stroke-width:2px
    style TPG fill:#bfb,stroke:#333,stroke-width:2px
    style SPT fill:#bfb,stroke:#333,stroke-width:2px
    style WST fill:#bfb,stroke:#333,stroke-width:2px
    style HF fill:#fbb,stroke:#333,stroke-width:2px
    style Slack fill:#fbb,stroke:#333,stroke-width:2px
```

The diagram shows:
- The main process that starts the agent system
- Two AI agents with their respective models
- The handoff relationship between the agents
- Three tools used by the agents
- External services that the tools interact with 