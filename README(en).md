# Foreword
- Who it suits: Users who need to frequently review their markdown notes (e.g., Obsidian) and those requiring quick access to local AI capabilities

# Feature Overview
1. Basic conversation (multi-turn dialogue history management)
2. Prompt features
    - System prompts: Global prompt configurations
    - Custom prompts: Quickly activate custom prompts using @
3. Knowledge base search functionality
    - Search-only mode: Displays the most relevant content from markdown note titles
    - RAG functionality: Enables AI responses combined with search results
4. Hotkey configuration
    - alt + s: Show/hide window
    - alt + q: Paste clipboard text to input box
5. Preview
![Project Screenshot](image.png)

# Quick Start
[Video Tutorial](https://www.bilibili.com/video/BV1qzAoeWEY4?t=5.6)
1. Configure the JSON files (three total): Set up LLM and embedding in config.json, with other files for prompt configuration
2. Run run.bat directly

# Local Environment Setup
1. Set up environment: Recommended to use conda virtual environment. Navigate to project directory and run:
   pip install -r requirements.txt
2. Configure models: LLM must support OpenAI-compatible interfaces, embedding only supports Ollama. Configure prompt templates (optional) in three JSON files
3. First-time setup: Run update_knowledge.py to initialize knowledge base (default: test_markdowns directory). Keep default for testing, see below for custom paths
4. Run main.py: Initial execution will load all markdown titles for indexing. To disable auto-loading, comment out vector_db.add_documents(docs) in search_module's get_vector_store() function (line 15)

# RAG Configuration
RAG implementation requires two components:
1. Knowledge base path configuration (via update_knowledge.py)
2. Title index loading (via search_module's get_vector_store() function)

## Custom Knowledge Base Path
- Modify line 132 in update_knowledge.py: Replace md_folder = "test_markdowns" with your markdown root directory

## Updating Title Index
1. Manually delete chroma_db folder
2. Execute main.py (if vector_db.add_documents(docs) remains uncommented, titles will reload automatically)

# Final Notes
- THis is my first-time project creation with zero prior experience - mostly AI-assisted. Your understanding and suggestions are appreciated!