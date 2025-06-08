from mcp import stdio_client, StdioServerParameters
from strands import Agent, tool
from strands.tools.mcp import MCPClient
from strands.models import BedrockModel
import boto3 
import os
import json
import requests
import re

LANG_SEARCH_TOKEN = os.environ.get("LANG_SEARCH_TOKEN", None)

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
    """Search the web for information about a given query

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
        tools.extend([weather, web_search])
        self.agent = Agent(
            tools=tools, 
            model=bedrock_model,
            system_prompt="You are a helpful assistant that can do web searches. Please include your response within the <response></response> tag."
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