# CLAUDE CODE INSTRUCTIONS

## FUNDAMENTAL PRINCIPLE: 90% SHARPEN THE AXE, 10% CUT THE TREE

**"Give me six hours to chop down a tree and I will spend the first four sharpening the axe." - Abraham Lincoln**

When dealing with complex systems like deployment toolchains, **preparation and analysis are crucial**:

### 90% Preparation Phase:
✅ **ALWAYS START WITH:**
- **Deep system analysis** - Understand the full workflow before coding
- **User journey mapping** - How will LLMs actually use these tools?
- **Edge case identification** - What can go wrong? (subdirectories, workspace selection, API failures)
- **Dependency understanding** - How do tools interact with each other?
- **Real-world testing** - Try the tools as an actual user would
- **Error handling design** - Plan for failures before they happen

### 10% Implementation Phase:
- Write the actual code
- Implement the solutions to identified problems
- Handle the edge cases you already discovered

### Why This Matters:

**Bad Approach (Rush to Code):**
```python
# Quick tool - doesn't handle subdirectories, assumes defaults
def deploy_app(name, repo):
    return create_service(name, repo)  # Missing workspace selection, structure detection
```

**Good Approach (Sharpen First):**
```python
# Well-designed tool after analysis
def deploy_app(name, repo, workspace_id, project_path):
    # 90% of work was thinking through these requirements:
    # - How to handle subdirectories?
    # - How to ensure workspace selection?
    # - How to detect project structure?
    # - How to integrate monitoring?
    # - How to handle real API failures?
```

### Real Example From This Project:

**Problems We Could Have Avoided:**
1. **Repository structure** - Should have analyzed: "Where do projects actually live?"
2. **Workspace selection** - Should have thought: "How do users actually choose workspaces?"
3. **Wait tool complexity** - Should have realized: "Do we really need a separate monitoring tool?"

**The Lesson:** Spending time upfront understanding the FULL user journey and system complexity saves massive amounts of rework later.

### Apply This To All Complex Systems:
- **Deployment pipelines** - Map the entire flow first
- **Database integrations** - Understand all connection patterns
- **Authentication systems** - Plan all user paths
- **API integrations** - Consider all failure modes

**Remember: 90% preparation, 10% implementation = Better tools, fewer bugs, happier users**

---

## CRITICAL: NO FAKE/SIMULATED API CALLS

**NEVER CREATE FAKE OR SIMULATED API CALLS**

This is an absolute rule with no exceptions. All deployment tools and API integrations MUST make real API calls.

### What is PROHIBITED:

❌ **NEVER DO THIS:**
- Creating fake service IDs like `srv-app-name-simulated`
- Simulating API responses with hardcoded values
- Using `await asyncio.sleep()` to fake processing time
- Returning mock success messages without real API calls
- Any form of simulation, mocking, or fake responses

### What is REQUIRED:

✅ **ALWAYS DO THIS:**
- Use real HTTP clients (aiohttp, requests, curl)
- Make actual API calls to external services
- Handle real errors and responses
- Return actual service IDs, URLs, and data from APIs
- Implement proper error handling for API failures

### Examples:

**WRONG - Simulated (NEVER DO THIS):**
```python
# This is FORBIDDEN
service_id = f"srv-{app_name}-simulated"
await asyncio.sleep(2)  # Fake processing
return {"status": "success", "id": service_id}
```

**CORRECT - Real API Call:**
```python
async with aiohttp.ClientSession() as session:
    async with session.post(api_url, headers=headers, json=payload) as response:
        if not response.ok:
            raise Exception(f"API error {response.status}: {await response.text()}")
        return await response.json()
```

### API Integration Rules:

1. **Always use real HTTP clients** - aiohttp for async, requests for sync
2. **Include proper authentication** - API keys, tokens, headers
3. **Handle real errors** - network failures, API errors, timeouts
4. **Return actual data** - real IDs, URLs, status from the API response
5. **Implement retries** - for transient failures when appropriate

### Testing Guidelines:

- If you need to test without affecting production, use:
  - Test/sandbox endpoints provided by the service
  - Development/staging environments
  - Dry-run parameters if supported by the API
- **NEVER** create fake responses as a testing mechanism

### Deployment Tools Specific Rules:

For Render, AWS, Vercel, or any deployment service:

1. Use the official API endpoints
2. Make real service creation calls
3. Monitor actual deployment status
4. Return real service URLs and IDs
5. Handle real deployment failures

### Violation Consequences:

Creating fake API calls is considered a critical bug that:
- Misleads users about the actual state of their deployments
- Breaks the user's trust in the system
- Can cause data loss or service outages
- Must be immediately fixed

### When Unsure:

If you're unsure about an API integration:
1. Read the official API documentation
2. Look at existing working examples in the codebase
3. Ask for clarification rather than creating fake calls
4. Err on the side of making real calls, even if they might fail

## TOOL DESIGN: LLM-FRIENDLY ONLY

**ALL TOOLS MUST BE DESIGNED FOR LLM USE, NOT HUMAN USE**

### Tool Documentation Requirements:

✅ **CORRECT - LLM-FRIENDLY:**
```python
def deploy_app(repo_url: str, workspace_id: str) -> str:
    """
    LLM INSTRUCTION: Deploy app to Render.

    LLM WORKFLOW:
    1. Call detect_git_repository() first
    2. Ask user: "Use this repo or provide different URL?"
    3. Call list_workspaces()
    4. Ask user to select workspace_id
    5. THEN call this tool

    LLM BEHAVIOR:
    - NEVER test locally (npm install, npm run dev)
    - Make REAL API calls only
    - Handle real errors gracefully

    CRITICAL: Makes real API calls to Render
    """
```

❌ **WRONG - HUMAN-FRIENDLY:**
```python
def deploy_app(repo_url: str, workspace_id: str) -> str:
    """
    Deploy your application to Render with ease!

    This tool helps you deploy your app quickly.
    Just provide your repo URL and workspace.
    """
```

### LLM-Friendly Documentation Rules:

1. **Start with "LLM INSTRUCTION:"** - Tell the LLM exactly what to do
2. **Include "LLM WORKFLOW:"** - Step-by-step instructions for the LLM
3. **Add "LLM BEHAVIOR:"** - Critical behavioral requirements
4. **Use "CRITICAL:" warnings** - For important constraints
5. **No human-friendly language** - No "helps you", "with ease", etc.

### Required LLM Instructions:

Every tool MUST include:
- **Never test locally** instructions
- **Real API calls only** warnings
- **Exact workflow steps** for the LLM to follow
- **Parameter requirements** and how to get them
- **Error handling** expectations

### Tool Parameter Design:

- **Always require explicit parameters** - No auto-detection
- **Force user choices** - Ask user for workspace_id, repo_url, etc.
- **No defaults without user consent** - Make users choose
- **Clear parameter descriptions** - Tell LLM how to get values

## REMEMBER: REAL CALLS ONLY, NO EXCEPTIONS

This rule applies to ALL external integrations:
- Cloud deployments (Render, Vercel, AWS, etc.)
- Database operations
- File storage services
- Payment processing
- Email services
- Any third-party APIs

**When in doubt, make the real call.**

## TOOL METADATA MUST BE LLM-FOCUSED

Never write tool descriptions for humans. Always write for LLM behavior.