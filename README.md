# Multi-Model Chatbot

This project is a multi-model AI chatbot with support for various AI modules, including image generation, speech-to-text, text-to-speech, and more. 

## Architecture

Below is a high-level architecture diagram of the Multi-Model Chatbot system:

![Architecture Diagram](architecture/Architecture.png)

*The diagram illustrates the flow between users, the chat interface, core AI modules (including Whisper, Llama, LangGraph, and memory components), and the types of data exchanged (messages, images, audio, etc.).*

## Features
- Image generation
- Image-to-text
- Speech-to-text
- Text-to-speech
- Long-term and short-term memory modules
- Chainlit interface for chat

## Note
**WhatsApp integration is currently not included in this version. All WhatsApp-related files and endpoints have been removed.**

## Getting Started
Instructions for setting up and running the chatbot locally:

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd Multi-Model-Chatbot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or, if using Poetry:
   ```bash
   poetry install
   ```
3. Run the local server:
   ```bash
   ./run_local.sh
   ```

## Directory Structure
- `src/ai_companion/` - Main source code
- `generated_images/` - Output images
- `logs/` - Log files
- `long_term_memory/` - Long-term memory storage
- `short_term_memory/` - Short-term memory (SQLite DB)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](LICENSE) 