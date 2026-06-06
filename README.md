# Team Type: Individual
# Team Member:
- Chirag Sindhu
- business.chiragsindhu@gmail.com

# Mytheos: Multi-Agent Yielding Traceback, Hypothesis, Evaluation, Optimization & Solutions

MYTHEOS (Multi-Agent Yielding Traceback, Hypothesis, Evaluation, Optimization & Solutions) is an autonomous debugging platform that leverages a swarm of specialized AI agents to investigate, diagnose, and repair software defects.

Modern software teams spend significant engineering effort reproducing bugs, analyzing stack traces, understanding code dependencies, identifying root causes, generating fixes, and validating solutions. While current AI coding assistants can generate snippets of code, they often lack structured reasoning, verification mechanisms, and collaborative workflows required for reliable debugging.

MYTHEOS introduces a multi-agent architecture where each agent specializes in a specific phase of the debugging lifecycle:
• Planner Agent – Analyzes the repository, issue description, and error logs to create a debugging strategy.
• Reproduction Agent – Attempts to reproduce failures through automated execution and test discovery.
• Code Analysis Agent – Examines code structure, dependency graphs, execution paths, and affected components.
• Context Agent – Retrieves relevant documentation, commit history, pull requests, and related issues.
• Root Cause Agent – Synthesizes evidence from other agents to determine the most probable cause of failure.
• Fix Agent – Generates targeted code modifications and remediation strategies.
• Test Agent – Creates regression tests and validates generated fixes.
• Review Agent – Evaluates security, maintainability, performance implications, and code quality before finalizing recommendations.

The agents communicate through a centralized orchestration layer, allowing evidence sharing, iterative validation, and collaborative decision-making. Instead of relying on a single AI response, MYTHEOS performs structured investigation similar to how experienced software engineering teams debug complex production issues.

Input:
• GitHub repository
• Bug report or issue description
• Error logs, stack traces, or failing test outputs

Output:
• Root cause analysis report
• Debugging timeline
• Suggested code fixes
• Generated regression tests
• Pull-request-ready patch
• Confidence score and validation report

The solution aims to reduce debugging time, improve software reliability, and demonstrate how agent swarms can automate complex engineering workflows through collaborative intelligence.

## Architecture
GitHub Repository + Error Logs
              │
              ▼
        Planner Agent
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
Reproduction  Code      Context
   Agent     Analysis    Agent
              Agent
                │
                ▼
        Root Cause Agent
                │
                ▼
            Fix Agent
                │
                ▼
           Test Agent
                │
                ▼
          Review Agent
                │
                ▼
      Bug Report + Pull Request

## Microsoft AI Stack
MYTHEOS leverages Microsoft technologies to orchestrate autonomous debugging workflows:

- Azure OpenAI Service for agent reasoning and code analysis
- Azure AI Foundry for model orchestration and evaluation
- GitHub Copilot for accelerated development
- Azure Container Apps for deployment
- Azure Monitor for observability and agent telemetry

## Key Features
- Multi-Agent Debugging Swarm
- Automated Root Cause Analysis
- Intelligent Bug Reproduction
- Context-Aware Code Understanding
- AI-Powered Fix Generation
- Automatic Regression Test Creation
- Pull-Request Ready Patches
- Confidence Scoring & Validation

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ChiragSindhu/mytheos_microsoftbuildaihackathon.git
cd mytheos_microsoftbuildaihackathon
```

### 2. Run the Setup Script

The setup script creates a virtual environment and installs all required dependencies.

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. Activate the Virtual Environment

**Linux / macOS**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and add the required API keys:

```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
GITHUB_TOKEN=your_github_token
```

### 5. Verify Installation

```bash
python -m cli.main providers
```

You should see all configured providers and their status.

---

## Quick Start

Debug a repository using an error log:

```bash
python -m cli.main debug \
  --repo https://github.com/user/repo \
  --error-log error.txt
```

Or provide the error directly:

```bash
python -m cli.main debug \
  --repo https://github.com/user/repo \
  --error-text "TypeError: Cannot read property 'map' of undefined"
```

---

## Python API

```python
from src.core.orchestrator import MYTHEOSOrchestrator
import asyncio

async def debug_example():
    orchestrator = MYTHEOSOrchestrator()

    result = await orchestrator.debug(
        repo_url="https://github.com/user/repo",
        error_log=open("error.txt").read(),
        repo_path="./local-repo",
        language="python"
    )

    print(result["bug_report"])
    print(result["pull_request"])

asyncio.run(debug_example())
```

---

## Testing Individual Files

### Easy Bug
```bash
python -m cli.main test-file examples/buggy_files/easy_bug.py
```

### Medium Bug
```bash
python -m cli.main test-file examples/buggy_files/medium_bug.py
```

### Hard Bug
```bash
python -m cli.main test-file examples/buggy_files/hard_bug.py
```

### Test a Custom File
```bash
python -m cli.main test-file my_script.py
```

### Disable Auto Execution
```bash
python -m cli.main test-file my_script.py --no-auto-run
```

### Verbose Mode
```bash
python -m cli.main test-file my_script.py -v
```
