# Voice Search Agent

This project combines Amazon Bedrock's Nova Sonic voice interaction capabilities with the Strands web search functionality to create a voice-enabled search assistant.

## Features

- Voice input/output using Amazon Bedrock's Nova Sonic model
- Web search capabilities using Strands agent
- Real-time audio streaming with barge-in support
- Location and weather information lookup
- Image search using both keyword and semantic similarity
- Local vector database for efficient image retrieval using Ollama and ChromaDB

## Prerequisites

- Python 3.8 or higher
- AWS account with access to Amazon Bedrock
- AWS credentials configured (either through environment variables or AWS CLI)
- Working microphone and speakers/headphones
- Ollama installed and running locally with the llava model

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd demo-project
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:
Either set them as environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```
Or configure them using the AWS CLI:
```bash
aws configure
```

## Usage

Run the voice search agent:
```bash
python voice_search_agent.py
```

To enable debug mode:
```bash
python voice_search_agent.py --debug
```

To index images for vector search:
```bash
python image_indexer.py --directory /path/to/images
```

The image indexer supports the following options:
- `--directory`, `-d`: Directory containing images to index (default: ./images)
- `--ollama-url`: Ollama API base URL (default: http://localhost:11434)
- `--model`: Ollama model name to use (default: llava)
- `--db-path`: Path to store the vector database (default: image_vectors)

Once the voice agent is running:
1. The application will start listening through your microphone
2. Speak your query naturally
3. The assistant will process your voice input, perform web searches as needed, and respond with voice output
4. You can search for images using natural language queries that will match based on semantic similarity
5. Press Enter to stop the session

## Architecture

The project consists of three main components:

1. **BedrockStreamManager**: Handles bidirectional streaming with Amazon Bedrock's Nova Sonic model for voice interaction.
2. **StrandsAgent**: Processes text queries through web search capabilities.
3. **ImageVectorizer**: Manages image indexing and semantic search using Ollama and ChromaDB.

The audio handling is managed by the **AudioStreamer** class, which:
- Captures microphone input
- Streams audio to Nova Sonic
- Plays back the assistant's responses

## Error Handling

The application includes comprehensive error handling for:
- Audio device issues
- Network connectivity problems
- AWS service errors
- Invalid queries or responses

Debug mode can be enabled to help troubleshoot issues by providing detailed logging.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.