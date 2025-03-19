# Data Flow and Error Handling

This diagram illustrates the data flow throughout the system and how errors are handled at different stages.

```mermaid
flowchart TD
    subgraph "Data Flow"
        direction LR
        
        Paper[/Paper Data/] --> |extracted from| Dataset[(HuggingFace Datasets)]
        Paper --> PaperObj[PaperData Object]
        PaperObj --> |handed off to| Summary[Summary Agent]
        Summary --> |generates| SummaryText[/Summary Text/]
        SummaryText --> Output[PaperSummaryOutput Object]
        Output --> |formatted for| Slack[/Slack Message/]
        Slack --> |posted to| Channel[Slack Channel]
        Output --> |returned to| User[User]
    end
```

```mermaid
stateDiagram-v2
    [*] --> InitAgents: Start Agent System
    
    InitAgents --> FetchPaper: Initialize Agents
    
    state FetchPaper {
        [*] --> CallDatasetAPI: Attempt to load dataset
        CallDatasetAPI --> CheckMainData: Check current dataset
        CheckMainData --> Success: Paper found
        CheckMainData --> TryLegacy: No papers found
        TryLegacy --> CheckLegacyData: Check legacy dataset
        CheckLegacyData --> Success: Paper found
        CheckLegacyData --> NoData: No papers found
        NoData --> [*]: Raise ValueError
        Success --> [*]: Return paper data
    }
    
    FetchPaper --> HandoffToSummary: Paper Found
    FetchPaper --> ErrorState: Error fetching paper
    
    HandoffToSummary --> GenerateSummary: Successful handoff
    HandoffToSummary --> ErrorState: Handoff failed
    
    GenerateSummary --> PostToSlack: Summary created
    GenerateSummary --> ErrorState: Error creating summary
    
    PostToSlack --> VerifyPosting: Attempt to post
    
    state VerifyPosting {
        [*] --> CheckSlackToken: Verify token exists
        CheckSlackToken --> InitClient: Token found
        CheckSlackToken --> SlackError: No token
        InitClient --> PostMessage: Initialize client
        PostMessage --> SlackSuccess: Message posted
        PostMessage --> SlackError: API error
        SlackSuccess --> [*]: Return success details
        SlackError --> [*]: Return error details
    }
    
    VerifyPosting --> SuccessState: Posting successful
    VerifyPosting --> PartialSuccess: Posting failed but summary created
    
    ErrorState --> [*]: Return error
    PartialSuccess --> [*]: Return summary but note Slack failure
    SuccessState --> [*]: Return complete success
```

The diagrams show:
1. The flow of data from HuggingFace datasets through the system to Slack and back to the user
2. The state transitions showing error handling at each stage of the process
3. How the system attempts to recover from certain errors (e.g., falling back to legacy datasets) 