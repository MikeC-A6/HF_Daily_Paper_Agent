# Improved Class Diagram

This improved class diagram uses standard UML notation to accurately represent the relationship between the classes and data models in the HF Daily Paper Agent system.

```mermaid
classDiagram
    %% Base classes from external libraries
    class BaseModel {
        <<Pydantic>>
        +model_validate()
        +model_dump()
    }
    
    class Agent {
        <<OpenAI Agents SDK>>
        +name: str
        +model: str
        +instructions: str
        +tools: List[Tool]
        +handoffs: List[Handoff]
        +output_type: Type
        +as_tool()
    }
    
    class RunContextWrapper {
        <<OpenAI Agents SDK>>
        +get_state()
        +set_state()
    }
    
    %% Data models
    class PaperData {
        +title: str
        +arxiv_id: str
        +upvotes: int
        +pdf_url: str
        +additional_info: Optional[str]
    }
    
    class PaperSummaryOutput {
        +title: str
        +arxiv_id: str
        +upvotes: int
        +pdf_url: str
        +summary: str
    }
    
    %% Agent implementations
    class OrchestratorAgent {
        <<Instance>>
        +name = "OrchestratorAgent"
        +model = "o3-mini"
        +tools = [get_top_paper_pdf_url]
        +handoffs = [paper_summary_handoff]
    }
    
    class PaperSummaryAgent {
        <<Instance>>
        +name = "PaperSummaryAgent"
        +model = "gpt-4o"
        +tools = [WebSearchTool, post_paper_to_slack]
        +output_type = PaperSummaryOutput
    }
    
    %% Handoff related
    class HandoffFunction {
        +agent: Agent
        +input_type: Type
        +on_handoff: Callable
        +tool_name: str
        +tool_description: str
    }
    
    %% Tool implementations
    class WebSearchTool {
        +execute(query: str): Dict
    }
    
    class get_top_paper_pdf_url {
        <<function>>
        +async execute(date: Optional[str]): Dict
    }
    
    class post_paper_to_slack {
        <<function>>
        +async execute(title: str, arxiv_id: str, upvotes: int, pdf_url: str, summary: str, channel: str): Dict
    }
    
    %% Function definitions
    class on_paper_handoff {
        <<function>>
        +async execute(ctx: RunContextWrapper, input_data: PaperData): None
    }
    
    %% Inheritance relationships
    BaseModel <|-- PaperData : inherits
    BaseModel <|-- PaperSummaryOutput : inherits
    Agent <|-- OrchestratorAgent : instantiates
    Agent <|-- PaperSummaryAgent : instantiates
    
    %% Association relationships
    OrchestratorAgent "1" --> "1" HandoffFunction : uses
    HandoffFunction "1" --> "1" PaperSummaryAgent : references
    HandoffFunction "1" --> "1" PaperData : defines input type
    HandoffFunction "1" --> "1" on_paper_handoff : calls on handoff
    OrchestratorAgent "1" --> "*" get_top_paper_pdf_url : uses as tool
    PaperSummaryAgent "1" --> "1" WebSearchTool : uses as tool
    PaperSummaryAgent "1" --> "1" post_paper_to_slack : uses as tool
    PaperSummaryAgent "1" --> "1" PaperSummaryOutput : produces as output
    
    %% Data transformation flow (not a standard UML relationship)
    %% This is represented as a dependency with a stereotype
    PaperData ..> PaperSummaryOutput : <<transforms data to>>
    
    %% Notes for clarity
    note for PaperData "Input model for handoff\nContains paper metadata"
    note for PaperSummaryOutput "Output model from summary agent\nContains summary in addition to metadata"
    note for HandoffFunction "Created by handoff() function\nEnables agent-to-agent delegation"
```

## Class Relationship Analysis

The diagram above clarifies the following key relationships:

1. **Inheritance**:
   - Both `PaperData` and `PaperSummaryOutput` inherit from Pydantic's `BaseModel`
   - They are **separate classes** that share a common parent, not derived from each other

2. **Instance Relationships**:
   - `OrchestratorAgent` and `PaperSummaryAgent` are instances of the SDK's `Agent` class
   - They are configured with different settings, tools, and purposes

3. **Data Flow**:
   - The dotted arrow with stereotype `<<transforms data to>>` shows that data flows from `PaperData` to `PaperSummaryOutput`
   - This is a logical transformation performed by the agent, not an inheritance relationship
   - The agent extracts fields from `PaperData` and adds a `summary` field to create `PaperSummaryOutput`

4. **Handoff Mechanism**:
   - `HandoffFunction` connects the two agents, defining how data flows between them
   - It specifies `PaperData` as the input type and references the callback function

This diagram uses standard UML notation while still illustrating the conceptual "transformation" of data that occurs during the handoff process. 