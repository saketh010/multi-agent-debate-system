"""
Verify all dependencies are installed and configured correctly.
Run this before starting the debate system to ensure everything works.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.11 or higher"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version >= (3, 11):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (requires 3.11+)")
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = {
        "langgraph": "LangGraph",
        "langchain": "LangChain",
        "boto3": "AWS Boto3",
        "tavily": "Tavily Search",
        "dotenv": "Python Dotenv",
        "rich": "Rich",
        "streamlit": "Streamlit"
    }
    
    all_installed = True
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (not installed)")
            all_installed = False
    
    if not all_installed:
        print("\n   Run: pip install -r requirements.txt")
    
    return all_installed


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n⚙️  Checking environment configuration...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("   ❌ .env file not found")
        print("   Run: copy .env.example .env")
        print("   Then edit .env with your credentials")
        return False
    
    print("   ✅ .env file exists")
    
    # Check for required variables
    with open(env_path) as f:
        content = f.read()
    
    checks = {
        "TAVILY_API_KEY": "Tavily API Key",
        "BEDROCK_MODEL_ID": "Bedrock Model ID"
    }
    
    all_set = True
    for var, name in checks.items():
        if var in content and not f"{var}=your_" in content and not f"{var}=" in content.split(f"{var}=")[1].split("\n")[0].strip():
            print(f"   ✅ {name} configured")
        else:
            print(f"   ⚠️  {name} (not configured or using placeholder)")
            all_set = False
    
    # Check AWS credentials
    aws_profile = "AWS_PROFILE" in content
    aws_keys = "AWS_ACCESS_KEY_ID" in content and "AWS_SECRET_ACCESS_KEY" in content
    
    if aws_profile:
        print("   ✅ AWS Profile configured (Okta mode)")
    elif aws_keys:
        print("   ✅ AWS Credentials configured (Direct mode)")
    else:
        print("   ⚠️  AWS credentials not configured")
        all_set = False
    
    return all_set


def check_aws_credentials():
    """Check if AWS credentials are available"""
    print("\n🔐 Checking AWS credentials...")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Try to create a session
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            print("   ✅ AWS credentials available")
            
            # Check if we can access Bedrock
            try:
                bedrock = session.client('bedrock-runtime', region_name='us-east-1')
                print("   ✅ Bedrock runtime client initialized")
                return True
            except ClientError as e:
                print(f"   ⚠️  Bedrock access issue: {e}")
                return False
        else:
            print("   ❌ No AWS credentials found")
            print("   Run: okta-aws-cli -p sandbox")
            print("   Or configure AWS credentials in .env")
            return False
            
    except ImportError:
        print("   ⚠️  boto3 not installed")
        return False
    except Exception as e:
        print(f"   ⚠️  Error checking credentials: {e}")
        return False


def check_tavily():
    """Check if Tavily API is configured"""
    print("\n🔍 Checking Tavily API...")
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and not tavily_key.startswith("your_"):
        print("   ✅ Tavily API key configured")
        
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            print("   ✅ Tavily client initialized")
            return True
        except Exception as e:
            print(f"   ⚠️  Tavily client error: {e}")
            print("   System will use mock data if Tavily is unavailable")
            return False
    else:
        print("   ⚠️  Tavily API key not configured")
        print("   System will use mock data instead")
        return False


def main():
    """Run all checks"""
    print("🔧 Multi-Agent Debate System - Environment Check")
    print("=" * 60)
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_aws_credentials(),
        check_tavily()
    ]
    
    print("\n" + "=" * 60)
    
    if all(checks[:3]):  # Critical checks
        print("✅ System is ready to run!")
        print("\nRun the system:")
        print("   Web Interface:  streamlit run streamlit_app.py")
        print("   CLI Interface:  python main.py")
    elif all(checks[:2]) and checks[2]:
        print("⚠️  System can run but some features may be limited")
        print("   AWS/Tavily issues detected - check configuration above")
    else:
        print("❌ System is not ready - please fix issues above")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
