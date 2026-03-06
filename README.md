# Multi-Agent Debate System

A multi-agent debate system built with **LangGraph**, **AWS Bedrock**, and **Tavily Search**. This system orchestrates structured debates between specialized AI agents, complete with evidence gathering, multi-round arguments, cross-examination, scoring, and final judgment.

## 🎯 Overview

The Multi-Agent Debate System enables AI agents to engage in structured technical debates. Three specialized agents—Architecture, Performance, and Security—debate a given topic through multiple rounds, backed by real-time evidence from Tavily Search, with evaluation and final judgment.

### Key Features

- ✅ **Multi-round debates** with configurable rounds (1-5)
- ✅ **Evidence-based arguments** using Tavily Search API
- ✅ **Cross-examination** between agents
- ✅ **Argument scoring** on 4 criteria (logic, evidence, accuracy, relevance)
- ✅ **Final judge verdict** with detailed reasoning
- ✅ **AWS Bedrock integration** using Claude 3 models
- ✅ **Okta AWS CLI support** for enterprise authentication
- ✅ **LangGraph orchestration** with state management and memory
- ✅ **Rich CLI interface** with formatted output
- ✅ **Streamlit web interface** with live debate visualization
- ✅ **Auto-save results** to timestamped files

## 🏗️ Architecture

### Agent Roles

| Agent | Focus Area | Expertise |
|-------|-----------|----------|
| **Architect Agent** | System Design | Scalability, architecture patterns, modularity |
| **Performance Agent** | Optimization | Latency, throughput, resource efficiency |
| **Security Agent** | Safety & Security | Vulnerabilities, attack surface, best practices |
| **Moderator Agent** | Flow Control | Initializes and manages debate phases |
| **Scoring Agent** | Evaluation | Scores arguments on multiple criteria |
| **Judge Agent** | Final Verdict | Analyzes all arguments and declares winner |

### Debate Workflow

```
1. Moderator Initialization
          ↓
2. Evidence Retrieval (Tavily Search)
          ↓
3. Round 1: Opening Arguments (3 agents)
          ↓
4. Round 2+: Counter Arguments (3 agents)
          ↓
5. Cross-Examination (6 critiques)
          ↓
6. Argument Scoring (4 criteria per agent)
          ↓
7. Judge Decision (final verdict)
          ↓
8. Results Saved
```

## 📋 Prerequisites

- **Python 3.11+**
- **AWS Account** with Bedrock access
- **Tavily API Key**
- **Okta AWS CLI** (optional, for Okta-based authentication)

## 🚀 Setup Instructions

### 1. Clone Repository

```bash
cd multi-agent-debate-system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

#### Option A: Using Okta AWS CLI (Recommended for Enterprise)

1. Copy the environment template:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your Tavily API key:
   ```bash
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

3. Authenticate with Okta before running:
   ```bash
   okta-aws-cli -p sandbox
   ```

4. Run the debate system:
   ```bash
   python main.py
   ```

#### Option B: Direct AWS Credentials

1. Copy the environment template:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and fill in:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   TAVILY_API_KEY=your_tavily_api_key
   ```

3. Run the debate system:
   ```bash
   python main.py
   ```

### 5. Get Tavily API Key

1. Visit [https://tavily.com/](https://tavily.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to your `.env` file

**Note:** The system will work without Tavily by using mock data, but real search results provide better arguments.

## 🎮 Usage

### Option 1: Web Interface (Recommended)

Run the Streamlit web interface for a beautiful visual experience with live debate updates:

```bash
streamlit run streamlit_app.py
```

Or use the convenience scripts:
- **Windows**: `run_streamlit.bat`
- **Linux/Mac**: `./run_streamlit.sh`

The web interface provides:
- 🎨 Beautiful visual design
- 📊 Live progress tracking during debates
- 🎯 Real-time argument display
- 📈 Score visualization with progress bars
- 🏆 Winner announcement with styled verdict
- 💾 One-click download of results

See [STREAMLIT.md](STREAMLIT.md) for detailed web interface documentation.

### Option 2: CLI Interface

Run the command-line interface for terminal-based debates:

```bash
python main.py
```

You'll be prompted to:
1. Enter a debate topic
2. Choose number of rounds (1-5, default: 2)
3. Watch the debate unfold in real-time

### Example Topics

- "Should startups adopt microservices architecture?"
- "Is serverless architecture better than containers for production?"
- "Should we use NoSQL or SQL databases for a social media platform?"
- "Is TDD worth the development overhead?"
- "Should AI code generation tools replace manual coding?"

## 📁 Project Structure

```
multi-agent-debate-system/
├── agents/                 # Agent implementations
│   ├── architect_agent.py # Architecture expert
│   ├── performance_agent.py # Performance expert
│   ├── security_agent.py  # Security expert
│   ├── moderator_agent.py # Flow control
│   ├── scoring_agent.py   # Argument evaluation
│   └── judge_agent.py     # Final verdict
├── graph/                  # LangGraph workflow
│   └── debate_graph.py    # Main orchestration
├── state/                  # State management
│   └── debate_state.py    # Shared state schema
├── tools/                  # External tools
│   └── tavily_search.py   # Evidence retrieval
├── prompts/                # Prompt templates
│   └── debate_prompts.py  # All agent prompts
├── utils/                  # Utilities
│   └── bedrock_client.py  # AWS Bedrock client
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | `us-east-1` | AWS region for Bedrock |
| `BEDROCK_MODEL_ID` | Yes | `anthropic.claude-3-sonnet-20240229-v1:0` | Claude model ID |
| `TAVILY_API_KEY` | No | - | Tavily search API key |
| `AWS_ACCESS_KEY_ID` | Conditional | - | AWS access key (if not using Okta) |
| `AWS_SECRET_ACCESS_KEY` | Conditional | - | AWS secret key (if not using Okta) |
| `AWS_SESSION_TOKEN` | Auto | - | Set by okta-aws-cli |
| `AWS_PROFILE` | Optional | - | AWS profile name |

### Available Bedrock Models

- `anthropic.claude-3-sonnet-20240229-v1:0` (Recommended - balanced)
- `anthropic.claude-3-haiku-20240307-v1:0` (Fast and cost-effective)
- `anthropic.claude-3-5-sonnet-20240620-v1:0` (Most capable)
- `anthropic.claude-3-opus-20240229-v1:0` (Highest quality)

## 📊 Output Format

The system provides:

1. **Real-time Display**: Formatted output in the terminal
2. **Saved Results**: Auto-saved to `debate_result_YYYYMMDD_HHMMSS.txt`

### Sample Output Structure

```
==========================================================
ARGUMENTS
==========================================================
ARCHITECT - Round 1
  Argument: [Architecture perspective with evidence]
  Evidence: [Citations and sources]
  
PERFORMANCE - Round 1
  Argument: [Performance perspective with evidence]
  ...

==========================================================
CROSS-EXAMINATIONS
==========================================================
ARCHITECT examining PERFORMANCE:
  [Critical analysis of performance claims]
...

==========================================================
SCORES
==========================================================
Agent: ARCHITECT
  Logical Reasoning:   8.5/10
  Evidence Quality:    7.8/10
  Technical Accuracy:  9.0/10
  Relevance:           8.2/10
  TOTAL SCORE:         33.5/40
...

==========================================================
FINAL VERDICT
==========================================================
🏆 WINNER: ARCHITECT

Summary: [Comprehensive debate summary]

Key Points:
  • [Point 1]
  • [Point 2]
  • [Point 3]

Reasoning: [Detailed explanation of decision]
```

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Type checking
mypy .

# Linting
flake8 .

# Formatting
black .
```

## 🐛 Troubleshooting

### AWS Credentials Issues

**Problem:** "No AWS credentials found"

**Solution:**
- If using Okta: Run `okta-aws-cli -p sandbox` before `python main.py`
- If using direct credentials: Check `.env` file has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Verify AWS region supports Bedrock: `us-east-1`, `us-west-2`, etc.

### Tavily API Issues

**Problem:** "Tavily search error"

**Solution:**
- Verify `TAVILY_API_KEY` in `.env` is correct
- Check API quota at https://tavily.com/
- System will fall back to mock data if Tavily unavailable

### Import Errors

**Problem:** "ModuleNotFoundError"

**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### LangGraph Issues

**Problem:** "Cannot import StateGraph"

**Solution:**
```bash
pip install langgraph>=0.2.0 --upgrade
```

## 📝 Example Session

```bash
$ python main.py

╭─────────────────────────────────────────╮
│  Multi-Agent Debate System              │
╰─────────────────────────────────────────╯

✓ Rich formatting enabled
✓ AWS credentials detected
  Using AWS session credentials (Okta-based)
✓ Tavily API key configured

Enter a debate topic (or press Ctrl+C to exit):
Example: Should startups adopt microservices architecture?

> Should startups adopt microservices architecture?

Number of debate rounds (default: 2):
> 2

╭─────────────────────────────────────────╮
│  Starting Debate: 2 Rounds              │
╰─────────────────────────────────────────╯

Topic: Should startups adopt microservices architecture?
Rounds: 2

Running debate workflow...

[Debate proceeds with arguments, cross-examinations, scoring, and verdict]

✓ Results saved to: debate_result_20260305_143522.txt
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

See [LICENSE](LICENSE) file for details.

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check troubleshooting section above
- Review example sessions

---
