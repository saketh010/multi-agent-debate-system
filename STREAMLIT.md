# Streamlit Web Interface Guide

Beautiful web-based interface for the Multi-Agent Debate System! 🎨

## 🌟 Features

✨ **Live Progress Tracking** - Watch debates unfold in real-time
✨ **Beautiful UI** - Styled cards and progress bars
✨ **Interactive Input** - Easy topic entry and round selection
✨ **Live Updates** - See arguments, cross-examinations, and scores as they happen
✨ **Download Results** - Save debate results with one click
✨ **Configuration Status** - See AWS and Tavily status at a glance
✨ **Responsive Design** - Works on desktop and mobile

## 🚀 Quick Start

### 1. Install Streamlit (if not installed)

```bash
pip install streamlit>=1.32.0
# Or reinstall all dependencies:
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file is set up with AWS credentials and Tavily API key:

```bash
# If using Okta:
okta-aws-cli -p sandbox

# Then verify .env has:
AWS_PROFILE=sandbox
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
TAVILY_API_KEY=your_key_here
```

### 3. Launch Streamlit App

```bash
streamlit run streamlit_app.py
```

Your browser will automatically open to `http://localhost:8501`

**Alternative:** Use the convenience script:
```bash
# On Windows:
run_streamlit.bat

# On macOS/Linux:
./run_streamlit.sh
```

## 📱 Using the Interface

### Main Page

1. **Check Sidebar** - Verify AWS and Tavily configuration
2. **Enter Topic** - Type your debate question
3. **Select Rounds** - Choose 1-5 rounds (2 recommended)
4. **Click "Start Debate"** - Watch the magic happen!

### During Debate

The interface shows:
- ✅ **Progress Bar** - Current phase of debate
- 💬 **Arguments** - Each agent's arguments appear as they're generated
- 🔍 **Cross-Examinations** - Critiques between agents
- 📊 **Scores** - Evaluation metrics with progress bars
- 🏆 **Final Verdict** - Judge's decision with reasoning

### After Debate

- 📥 **Download Results** - Click button to save full debate transcript
- 🔄 **Start New Debate** - Refresh page or enter new topic

## 🎨 Interface Sections

### Header
- Title and description
- Quick status overview

### Sidebar
- **Configuration Status**
  - AWS credentials check
  - Tavily API status
  - Model information
- **Active Agents**
  - Architect (🏗️)
  - Performance (⚡)
  - Security (🔒)
- **About & Documentation**

### Main Area
- **Topic Input** - Large text field for debate question
- **Rounds Selector** - Dropdown for 1-5 rounds
- **Example Topics** - Expandable list of suggestions
- **Start Button** - Begins debate process
- **Progress Section** - Real-time updates
- **Results Area** - Arguments, examinations, scores, verdict

## 💡 Tips for Best Experience

### Performance
- **Start with 2 rounds** - Good balance of depth and speed
- **Close other tabs** - For better performance
- **Use good internet** - AWS Bedrock needs stable connection

### Debugging
- **Check browser console** - F12 for JavaScript errors
- **Watch terminal** - See backend logs in terminal running Streamlit
- **Refresh if stuck** - F5 to restart

### Custom Styling
The app includes custom CSS for:
- Color-coded agent cards
- Gradient score cards
- Winner announcement styling
- Progress bar colors

## 🔧 Configuration Options

### Environment Variables (.env)

```bash
# AWS Configuration
AWS_PROFILE=sandbox
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Search API
TAVILY_API_KEY=your_key

# Optional: Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Streamlit Config (.streamlit/config.toml)

Create `.streamlit/config.toml` for advanced settings:

```toml
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[browser]
gatherUsageStats = false
```

## 🎯 Example Usage

### Example 1: Quick Debate

```bash
# Start Streamlit
streamlit run streamlit_app.py

# In browser:
Topic: "Should we use TypeScript or JavaScript?"
Rounds: 2
Click: Start Debate
```

### Example 2: Deep Analysis

```bash
# In browser:
Topic: "Best database for a social media platform at scale?"
Rounds: 4
Click: Start Debate

# Wait for comprehensive analysis
# Download results when complete
```

## 📊 Visual Features

### Agent Cards
- **Architect** - Blue border (🏗️)
- **Performance** - Green border (⚡)
- **Security** - Orange border (🔒)

### Progress Indicators
- Phase name displayed
- Progress bar (0-100%)
- Status emoji (🔄, ✅, ❌)

### Score Visualization
- Individual criterion bars
- Total score display
- Ranked by performance
- Color-coded feedback

### Final Verdict
- Gradient card design
- Trophy emoji for winner
- Collapsible sections
- Download button

## 🚦 Status Indicators

| Indicator | Meaning |
|-----------|---------|
| ✅ Green | Configured and working |
| ⚠️ Yellow | Warning or using fallback |
| ❌ Red | Not configured or error |

## 🔄 Workflow Comparison

### CLI (main.py)
```
python main.py
> Enter topic
> Enter rounds
> Watch text output
> Results saved to file
```

### Web (streamlit_app.py)
```
streamlit run streamlit_app.py
→ Beautiful web interface
→ Interactive inputs
→ Live progress visualization
→ One-click download
```

## 📦 Deployment Options

### Local Development
```bash
streamlit run streamlit_app.py
```

### Network Access
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
```

### Streamlit Cloud (Free)
1. Push to GitHub
2. Connect at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Deploy with one click
4. Share public URL

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

## 🐛 Troubleshooting

### "Page not loading"
```bash
# Check if port 8501 is available
netstat -an | findstr 8501

# Use different port
streamlit run streamlit_app.py --server.port 8502
```

### "AWS credentials not found"
```bash
# Authenticate with Okta first
okta-aws-cli -p sandbox

# Then start Streamlit
streamlit run streamlit_app.py
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### "Debate stuck/not progressing"
- Refresh the page (F5)
- Check terminal for errors
- Verify AWS Bedrock access
- Check model availability

## 🎨 Customization

### Change Colors
Edit the `<style>` section in `streamlit_app.py`:

```python
st.markdown("""
    <style>
    .main-header {
        color: #YOUR_COLOR;
    }
    </style>
""", unsafe_allow_html=True)
```

### Add New Sections
```python
def display_custom_section():
    st.markdown("## Your Section")
    st.write("Content here")

# Call in main():
display_custom_section()
```

### Modify Layout
```python
# Change from wide to centered
st.set_page_config(layout="centered")

# Change columns
col1, col2, col3 = st.columns([2, 3, 2])
```

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Gallery](https://streamlit.io/gallery)
- [Streamlit Cheat Sheet](https://docs.streamlit.io/library/cheatsheet)
- [Project README](README.md)

## 🆚 CLI vs Web Comparison

| Feature | CLI | Streamlit |
|---------|-----|-----------|
| User Interface | Terminal | Web Browser |
| Input | Text prompts | Forms/Inputs |
| Progress | Text updates | Progress bar |
| Visuals | Plain text | Styled cards |
| Results | File output | Download button |
| Accessibility | Terminal access | Browser access |
| Best For | Automation | Interactive use |

## 🎉 Next Steps

1. ✅ Install Streamlit
2. ✅ Configure environment
3. ✅ Launch app
4. ✅ Run first debate
5. ✅ Explore features
6. ✅ Customize styling
7. ✅ Share with team!

---

**Happy Debating in Style! 🎨⚖️**
