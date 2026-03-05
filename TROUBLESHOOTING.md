# Troubleshooting Guide

## Common Issues and Solutions

### ❌ Error: "ValidationException: Invocation of model ID ... with on-demand throughput isn't supported"

**Problem:**
```
Bedrock API call failed: An error occurred (ValidationException) when calling the InvokeModel 
operation: Invocation of model ID anthropic.claude-3-7-sonnet-20250219-v1:0 with on-demand 
throughput isn't supported. Retry your request with the ID or ARN of an inference profile 
that contains this model.
```

**Cause:**
Some newer Claude models (like Claude 3.5 Sonnet, Claude 3.7, etc.) require using inference profile ARNs instead of direct model IDs for invocation.

**Solution:**
Update your `.env` file to use a supported on-demand model ID:

```bash
# ✅ WORKING - Direct model IDs (on-demand compatible)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0    # Claude 3 Sonnet (recommended)
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0     # Claude 3 Haiku (faster, cheaper)
BEDROCK_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0      # Claude 3 Opus (most capable)

# ✅ WORKING - Inference Profile ARNs (for newer models)
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20240620-v1:0
```

**Quick Fix:**
```bash
# Open .env file and change:
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Then restart:
python main.py
```

---

### ❌ Error: "No AWS credentials found"

**Problem:**
```
! No AWS credentials found
If using Okta: Run 'okta-aws-cli -p sandbox' first
```

**Solution:**

**If using Okta:**
```bash
# Authenticate first (do this in every new terminal session)
okta-aws-cli -p sandbox

# Then run the debate
python main.py
```

**If using direct credentials:**
Add to `.env`:
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

**If using AWS profile:**
Add to `.env`:
```bash
AWS_PROFILE=your_profile_name
AWS_REGION=us-east-1
```

---


### ❌ Error: "AccessDeniedException" from Bedrock

**Problem:**
```
botocore.errorfactory.AccessDeniedException: An error occurred (AccessDeniedException) 
when calling the InvokeModel operation: User is not authorized to perform: 
bedrock:InvokeModel on resource
```

**Cause:**
Your AWS account or IAM role doesn't have Bedrock permissions.

**Solution:**

1. **Check Bedrock is enabled in your region:**
   - Go to AWS Console → Bedrock
   - Check if service is available
   - Enable model access if needed

2. **Add IAM permissions:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:ListFoundationModels"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

3. **Verify region supports Bedrock:**
   Supported regions: `us-east-1`, `us-west-2`, `eu-west-1`, `ap-southeast-1`, etc.

---

### ⚠️ Warning: "Core Pydantic V1 functionality isn't compatible with Python 3.14"

**Problem:**
```
UserWarning: Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

**Impact:** This is just a warning, not an error. The system will still work.

**Solution (optional):**
- Use Python 3.11 or 3.12 for best compatibility
- Or ignore the warning (it doesn't affect functionality)

---

## Supported Model IDs Reference

### ✅ On-Demand Compatible (Direct Model IDs)

```bash
anthropic.claude-3-sonnet-20240229-v1:0    
anthropic.claude-3-haiku-20240307-v1:0    
anthropic.claude-3-opus-20240229-v1:0      
```

### ✅ Inference Profile ARNs (For Newer Models)

```bash
# Claude 3.5 Sonnet (US regions)
us.anthropic.claude-3-5-sonnet-20241022-v2:0
us.anthropic.claude-3-5-sonnet-20240620-v1:0

# Claude 3.5 Sonnet (EU regions)
eu.anthropic.claude-3-5-sonnet-20240620-v1:0

# Note: Profile ARNs are region-specific
# Format: {region-prefix}.{model-id}
```

---

## Getting Help

1. **Check this troubleshooting guide first**
2. **Review README.md** for setup instructions
3. **Check QUICKSTART.md** for common workflows
4. **Verify .env configuration** matches .env.example
5. **Test AWS credentials** with `aws sts get-caller-identity`
6. **Check Bedrock model availability** in your region
7. **Open an issue on GitHub** with full error message

---

**Last Updated:** March 5, 2026
