# GenAI Cold Email Generator Architecture

```mermaid
graph TD
    subgraph "Frontend"
        UI[Streamlit UI]
        UI --> |Job URL Input| WS[WebScraper]
    end

    subgraph "Data Processing"
        WS --> |Raw HTML| CT[clean_text]
        CT --> |Cleaned Text| Chain
        P[Portfolio] --> |Skills & Links| Chain
    end

    subgraph "LLM Integration"
        Chain --> |API Request| Groq[Groq LLM API]
        Groq --> |Rate Limit: 100k tokens/day| Chain
        Chain --> |Job Data| JE[Job Extraction]
        Chain --> |Email Generation| EG[Email Generation]
    end

    subgraph "Data Storage"
        P --> |Read| CSV[my_portfolio.csv]
    end

    subgraph "Core Components"
        WS --> |Fetch| Static[Static Content]
        WS --> |Dynamic| Selenium[Selenium WebDriver]
        DE[Deadline Extractor] --> |Date Analysis| Chain
    end

    JE --> |Skills & Requirements| UI
    EG --> |Generated Email| UI
    DE --> |Application Deadline| UI

    classDef primary fill:#2374e1,stroke:#fff,stroke-width:2px,color:#fff
    classDef secondary fill:#164e87,stroke:#fff,stroke-width:2px,color:#fff
    classDef storage fill:#ff9900,stroke:#fff,stroke-width:2px,color:#fff
    
    class UI,Chain primary
    class WS,CT,P,JE,EG,DE secondary
    class CSV,Groq storage
```

## Component Description

### Frontend
- **Streamlit UI**: Web interface for user interaction and result display
- **WebScraper**: Handles URL fetching with both static and dynamic content support

### Data Processing
- **clean_text**: Text preprocessing and sanitization
- **Portfolio**: Manages skills and project links from CSV data
- **Chain**: Orchestrates the entire workflow

### LLM Integration
- **Groq LLM API**: 
  - Handles natural language processing tasks
  - Rate limit: 100,000 tokens per day
  - Used for job extraction and email generation

### Data Storage
- **my_portfolio.csv**: Stores portfolio data, skills, and relevant links

### Core Components
- **Deadline Extractor**: Specialized component for finding application deadlines
- **Static Content Fetcher**: Basic HTTP requests for simple pages
- **Selenium WebDriver**: Handles JavaScript-heavy pages

## Data Flow
1. User inputs job URL
2. WebScraper fetches and processes the page
3. Text is cleaned and analyzed
4. Job details are extracted using LLM
5. Portfolio data is matched with job requirements
6. Cold email is generated using LLM
7. Results are displayed in UI

## Key Considerations
- Token usage monitoring and optimization
- Graceful handling of rate limits
- Caching opportunities for repeated requests
- Fallback strategies for LLM availability