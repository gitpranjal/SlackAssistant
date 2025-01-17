# Slack Assistant Project

This project is a Slack-integrated AI Assistant that analyzes Slack channels, summarizes conversations, filters out relevant channels based on user-inputted topics, and provides intelligent responses using Retrieval-Augmented Generation (RAG). The assistant leverages Slack API for fetching messages and shared files while ensuring data privacy by running the AI model locally.

---

## Prerequisites

1. **Anaconda/Miniconda**: Ensure you have Anaconda or Miniconda installed on your system.
2. **Python 3.11**: The project requires Python version 3.11.
3. **Ollama**: The project uses Ollama to run Llama models locally. Ensure you have Ollama installed.
4. **Slack API Token**: Set up a Slack app in your workspace, define appropriate OAuth scopes, and retrieve the token.

---

## Setting Up Slack API

1. **Create a Slack App**:
   - Visit [Slack API Apps](https://api.slack.com/apps) and create a new app in your workspace.

2. **Define OAuth Scopes**:
   - Add the following bot token scopes to the app:
     - `channels:read`, `groups:read`, `channels:history`, `groups:history`, `files:read`, `chat:write`, `commands`

3. **Install the App**:
   - Install the app in your Slack workspace and copy the OAuth token.

4. **Set Up `.env`**:
   - Create a `.env` file in the project root and add your Slack token:
     ```env
     SLACK_TOKEN=xoxb-your-slack-token
     ```

For detailed steps on setting up a Slack bot, visit the [Slack Bot Setup Guide](https://github.com/UpMortem/slack-bot?tab=readme-ov-file).

---

## Automated Setup and Run

The project includes Bash scripts to streamline the setup and execution process:

### `setup.sh`

```bash
#!/bin/bash

# Remove existing environment
conda env remove -n slackenv

# Create new environment
conda env create -f environment.yml

echo "Environment setup complete. Activate it using: conda activate slackenv"
```

### `run.sh`

```bash
#!/bin/bash

# Activate the environment
conda activate slackenv

# Run the Slack Assistant application
python chat_window.py
```

---

## Usage Instructions

1. **Set up the environment**:
   ```bash
   bash setup.sh
   ```

2. **Run the application**:
   ```bash
   bash run.sh
   ```

3. **Activate the environment manually (optional)**:
   ```bash
   conda activate slackenv
   ```

---

## Features

### Slack Integration
- Fetches messages and shared files from public and private channels.
- Summarizes conversations for specified channels.
- Filters out relevant channels based on user-inputted topics.

### Retrieval-Augmented Generation (RAG)
- Initializes a Chroma vector store with dummy data to handle Slack messages.
- Vectorizes Slack channel messages and updates the vector store dynamically.
- Retrieves relevant conversations to provide accurate, context-aware responses.

### Localized AI
- Runs the Llama 3.2 model locally using Ollama.
- Ensures data privacy by avoiding any external cloud dependency.

### Intelligent Responses
- Combines LLM fallback responses with Slack-based insights.
- Summarizes Slack channels with detailed descriptions and shared file content.

### File Analysis
- Reads and includes the content of files shared on Slack channels in its summaries and analyses.

---

## Project Structure

- **`chat_window.py`**: The entry point for the chatbot interface.
- **`RAG/`**: Implements Retrieval-Augmented Generation and manages vector store logic.
- **`slack_handler.py`**: Handles Slack API integration for fetching channel data, messages, and files.
- **`model_handler.py`**: Coordinates Slack message analysis and RAG integration for intelligent responses.
- **`knowledge_base/`**: Stores Slack channel messages and files locally.
- **`environment.yml`**: Defines the dependencies required for the project.
- **`setup.sh` & `run.sh`**: Scripts for setting up and running the project.

---

## How It Works

### Slack Message Handling
- **Fetch Messages**: Uses the Slack API to fetch messages and shared files from specified channels.
- **Analyze Files**: Downloads shared files and integrates their content into Slack message summaries.
- **Summarize Conversations**: Produces intelligent summaries and insights for Slack channels.

### Retrieval-Augmented Generation (RAG)
- **Initialization**: Initializes a Chroma vector store with a dummy dataset.
- **Slack Data Integration**: Processes Slack messages, vectorizes them, and updates the vector store.
- **Query Execution**: Retrieves the most relevant conversations based on user queries.

---

## Example User Queries

- **Analyze a Slack Channel**:
  ```
  Analyze Slack channel #general
  ```
- **List Relevant Channels**:
  ```
  Find channels related to project discussions.
  ```
- **Summarize a Channel**:
  ```
  Describe Slack channel #announcements
  ```

---

## Security and Confidentiality

- **Local Processing**: Ensures data privacy by running the AI model and vector store locally.
- **No Cloud Dependency**: Avoids sending any Slack data to external servers, making it suitable for confidential company information and secure communication analysis.

---

Start analyzing and gaining insights from your Slack workspace with this intelligent assistant!

Refer to this link for more info about setting up slack bot
https://github.com/UpMortem/slack-bot?tab=readme-ov-file


