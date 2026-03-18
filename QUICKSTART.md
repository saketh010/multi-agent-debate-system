# Quick Start Guide - Multi-Agent Debate System

Get up and running in 5 minutes! 🚀

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] AWS Bedrock access enabled
- [ ] Okta AWS CLI configured (if using Okta authentication)
- [ ] Tavily API key (get free at https://tavily.com/)

## Step-by-Step Setup

### 1️⃣ Create Virtual Environment

```bash
# Navigate to project directory
cd multi-agent-debate-system

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `langgraph` - Agent orchestration
- `langchain` - LLM framework
- `boto3` - AWS SDK
- `tavily-python` - Search API
- `python-dotenv` - Environment variables
- `rich` (optional) - Pretty CLI output

### 3️⃣ Configure Environment

#### Option A: Using Okta (Recommended) ✅

1. **Copy environment template:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file:**
   ```bash
   # Only add your Tavily API key:
   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxx

   # Required for Streamlit image upload feature:
   S3_IMAGE_BUCKET_NAME=your-debate-image-bucket
   
   # Keep these as-is:
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   ```

3. **Authenticate with Okta before each session:**
   ```bash
   okta-aws-cli -p sandbox
   ```
   
   This command:
   - Opens your browser for Okta login
   - Sets AWS_ACCESS_KEY_ID automatically
   - Sets AWS_SECRET_ACCESS_KEY automatically
   - Sets AWS_SESSION_TOKEN automatically
   - Valid for 1 hour (typical)

4. **Run the debate:**
   ```bash
   python main.py
   ```

#### Option B: Direct AWS Credentials

1. **Copy environment template:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file with all credentials:**
   ```bash
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   TAVILY_API_KEY=tvly-...
   S3_IMAGE_BUCKET_NAME=your-debate-image-bucket
   ```

3. **Run the debate:**
   ```bash
   python main.py
   ```

### 4️⃣ Get Tavily API Key

1. Go to https://tavily.com/
2. Click "Get Started" or "Sign Up"
3. Create free account
4. Copy your API key from dashboard
5. Add to `.env` file:
   ```
   TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxx
   ```

**Note:** Free tier includes 1,000 searches/month - plenty for testing!

### 5️⃣ Run Your First Debate

```bash
python main.py
```

You'll see:
```
╭─────────────────────────────────────╮
│  Multi-Agent Debate System          │
╰─────────────────────────────────────╯

✓ Rich formatting enabled
✓ AWS credentials detected
  Using AWS session credentials (Okta-based)
✓ Tavily API key configured

Enter a debate topic (or press Ctrl+C to exit):
Example: Should startups adopt microservices architecture?

> 
```

## Example Topics to Try

1. **Architecture:** "Should startups adopt microservices architecture?"
2. **Database:** "Is NoSQL better than SQL for social media platforms?"
3. **DevOps:** "Should we use Kubernetes or serverless for production?"
4. **Development:** "Is Test-Driven Development worth the overhead?"
5. **AI/ML:** "Should companies use AI code generation tools in production?"
6. **Security:** "Is zero-trust architecture necessary for all organizations?"

## Typical Workflow

```bash
# 1. Activate virtual environment
venv\Scripts\activate

# 2. Authenticate with Okta (if using Okta)
okta-aws-cli -p sandbox

# 3. Run debate
python main.py

# 4. Enter topic when prompted
> Should startups adopt microservices architecture?

# 5. Choose rounds (or press Enter for default)
> 2

# 6. Watch the debate!
# Results automatically saved to debate_result_YYYYMMDD_HHMMSS.txt
```

## Troubleshooting

### Issue: "No AWS credentials found"

**If using Okta:**
```bash
# Run this BEFORE python main.py:
okta-aws-cli -p sandbox
```

**If using direct credentials:**
- Check `.env` file has `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Verify credentials are correct in AWS Console

### Issue: "Import langgraph could not be resolved"

```bash
# Reinstall dependencies:
pip install -r requirements.txt --upgrade
```

### Issue: "Tavily search error"

- Verify API key is correct in `.env`
- Check you haven't exceeded free tier limit
- System will automatically use mock data if Tavily fails

### Issue: Okta session expired

```bash
# Just re-authenticate:
okta-aws-cli -p sandbox

# Then run again:
python main.py
```

### Issue: "Bedrock access denied"

- Verify your AWS account has Bedrock enabled
- Check region supports Bedrock: `us-east-1`, `us-west-2`, `eu-west-1`, etc.
- Verify IAM permissions for Bedrock API access

## Pro Tips 💡

1. **Rich Output:** Install `rich` for beautiful CLI formatting:
   ```bash
   pip install rich
   ```

2. **Multiple Rounds:** Try 3-5 rounds for deeper debates:
   ```
   > 3
   ```

3. **Save Environment:** Keep your `.env` file local and never commit it:
   ```bash
   # Already in .gitignore
   ```

4. **Okta Aliases:** Create a shell alias for Okta auth:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc:
   alias aws-login="okta-aws-cli -p sandbox"
   ```

5. **Review Results:** All debates are saved with timestamps:
   ```
   debate_result_20260305_143522.txt
   ```

## Next Steps

- ✅ Run your first debate
- ✅ Try different topics
- ✅ Experiment with multiple rounds
- ✅ Review saved results
- ✅ Customize agent prompts in `prompts/debate_prompts.py`
- ✅ Adjust scoring criteria in `agents/scoring_agent.py`

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [.env.example](.env.example) for configuration options
- Open an issue on GitHub for bugs

---

**Happy Debating! 🎯**
