from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
import boto3 
import os
import json
import requests
import re
from PIL import Image
from pathlib import Path
from dotenv import load_dotenv
from image_vectorizer import ImageVectorizer

load_dotenv("../.env")
LANG_SEARCH_TOKEN = os.environ.get('LANG_SEARCH_TOKEN', '')
IMAGES_DIR = os.environ.get('IMAGES_DIR', Path(__file__).parent.parent / "images")
IMAGE_VECTORS = os.environ.get('IMAGE_VECTORS_DIR', (Path(__file__).parent.parent / "image_vectors").absolute().as_posix())

print(IMAGES_DIR)
print(IMAGE_VECTORS)


# Initialize image vectorizer
image_vectorizer = ImageVectorizer(db_path=IMAGE_VECTORS)

@tool
def vector_search_images(query: str) -> str:
    """Search for local images using semantic similarity to the text query and open it.
    
    Args:
        query: Text description of the desired image
        num_results: Number of results to return (default: 5)
    
    Returns:
        str: JSON string containing found images and their similarity scores
    """
    try:
        results = image_vectorizer.search_images(query, n_results=1)
        
        print(f"Found {results} for query '{query}'")
        # Format results for display
        response = {
            "query": query,
            "results": []
        }
        
        for result in results:
            # Try to verify the image exists and is valid
            try:
                with Image.open(result["image_path"]) as img:
                    img.show()
                    response["results"].append({
                        "path": result["image_path"],
                        "similarity": f"{result['similarity_score']:.3f}",
                        "metadata": result["metadata"]
                    })
            except Exception as e:
                print(f"Warning: Could not verify image {result['image_path']}: {e}")
                continue
        response_string = json.dumps(response, indent=2)
        print(f"Returning response: {response_string}")
        return response_string
    except Exception as e:
        return f"Error searching images: {str(e)}"

# @tool
# def search_images(keyword: str) -> str:
#     """Search for images in the images directory using keywords.
    
#     Args:
#         keyword: The keyword to search for in image filenames
    
#     Returns:
#         str: Path to the found image or error message if not found
#     """
#     # Ensure images directory exists
#     if not os.path.exists(IMAGES_DIR):
#         os.makedirs(IMAGES_DIR)
    
#     # Convert keyword to lowercase for case-insensitive search
#     keyword = keyword.lower()

#     print(f"Searching for images with keyword: {keyword}")
    
#     # Search for images with the keyword in their filename
#     found_images = []
#     for file in os.listdir(IMAGES_DIR):
#         if file.lower().find(keyword) != -1 and any(file.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
#             found_images.append(file)
    
#     if not found_images:
#         return f"No images found matching keyword: {keyword}"
    
#     # Return the path of the first matching image
#     image_path = os.path.join(IMAGES_DIR, found_images[0])
    
#     try:
#         # Try to open the image to verify it's valid
#         with Image.open(image_path) as img:
#             img.show()  # This will open the image in the default image viewer
#         return f"Found and opened image: {image_path}"
#     except Exception as e:
#         return f"Error opening image {image_path}: {str(e)}"

@tool
def weather(lat, lon: float) -> str:
    """Get weather information for a given lat and lon

    Args:
        lat: latitude of the location
        lon: logitude of the location
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": str(lat),
        "longitude": str(lon),
        "current_weather": True
    }
    response = requests.get(url, params=params)
    return response.json()["current_weather"]

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r
    
@tool
def web_search(query: str) -> str:
    """Search the web for information about a given query. Cannot do image search.

    Args:
        query: The search query string
    """
    # Using DuckDuckGo API for web search
    url = "https://api.langsearch.com/v1/web-search"
    params = {
        "query": query,
        "freshness": "onLimit",
        "summary": True,
        "count": 1
    }
    basic = BearerAuth(LANG_SEARCH_TOKEN)
    response = requests.post(url, json=params, auth=basic)
    result = response.json()
    
    # Extract relevant information from the response
    abstract = result.get("data", {}).get("webPages", {}).get("value", [{}])[0].get("summary", "")
    # if not abstract:
    #     # If no abstract, try getting related topics
    #     related_topics = result.get("RelatedTopics", [])
    #     if related_topics:
    #         # Get text from first related topic
    #         abstract = related_topics[0].get("Text", "")
    print(f"Web search result for query '{query}': {abstract}")
    return abstract if abstract else "No relevant information found."

class StrandsAgent:

    def __init__(self):
        # Launch AWS Location Service MCP Server and create a client object
        aws_profile = os.getenv("AWS_PROFILE")
        env = {"FASTMCP_LOG_LEVEL": "ERROR"}
        if aws_profile:
            env["AWS_PROFILE"] = aws_profile

        self.aws_location_srv_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(
                command="uvx", 
                args=["awslabs.aws-location-mcp-server@latest"],
                env=env)
            ))
        self._server_context = self.aws_location_srv_client.__enter__()
        self.aws_location_srv_tools = self.aws_location_srv_client.list_tools_sync()

        session = boto3.Session(
            region_name='us-east-1',
        )
        # Specify Bedrock LLM for the Agent
        bedrock_model = BedrockModel(
            model_id="amazon.nova-lite-v1:0",
            boto_session=session
        )
        # Create a Strands Agent with web search capabilities
        tools = self.aws_location_srv_tools
        tools.extend([weather, web_search, vector_search_images])
        self.agent = Agent(
            tools=tools, 
            model=bedrock_model,
            system_prompt="You are a helpful assistant that can do web searches and search for local images using semantic similarity. For semantic image search, use vector_search_images. Please include your response within the <response></response> tag."
        )

    def query(self, input):
        output = str(self.agent(input))
        if "<response>" in output and "</response>" in output:
            match = re.search(r"<response>(.*?)</response>", output, re.DOTALL)
            if match:
                output = match.group(1)
        elif "<answer>" in output and "</answer>" in output:
            match = re.search(r"<answer>(.*?)</answer>", output, re.DOTALL)
            if match:
                output = match.group(1)
        return output

    def call_tool(self, tool_name, input):
        if isinstance(input, str):
            input = json.loads(input)
        if "query" in input:
            input = input.get("query")

        tool_func = getattr(self.agent.tool, tool_name)
        return tool_func(query=input)

    def close(self):
        # Cleanup the MCP server context
        self.aws_location_srv_client.__exit__(None, None, None)