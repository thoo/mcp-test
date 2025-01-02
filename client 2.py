import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger
load_dotenv()  # load environment variables from .env
from rich.logging import RichHandler

logger.configure(handlers=[{"sink": RichHandler(markup=True),
                         "format": "[red]{function}[/red] {message}"}])
logger.add('multi_tools.log')
COT_INSTRUCTION="""Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within \<thinking>\</thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. For example, find coordiantes of the popular cities yourself. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.
"""
class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools=[]

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"\nConnected to server with tools: {[tool.name for tool in tools]}")
        self.available_tools = [{ 
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in response.tools]

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        # Process response and handle tool calls
        tool_results = []
        final_text = []

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Continue conversation with tool results
                if hasattr(content, 'text') and content.text:
                    messages.append({
                      "role": "assistant",
                      "content": content.text
                    })
                messages.append({
                    "role": "user", 
                    "content": result.content
                })

                logger.info(f"{messages=}")
                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                )

                final_text.append(response.content[0].text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop that maintains conversation context"""
        logger.info("\nMCP Client Started!")
        logger.info("Type your queries or 'quit' to exit.")
        
        # Initialize conversation state
        system_prompt = """
        You are a helpful assistant with access to various tools.
        Be helpful and brief in your responses.
        Only use tools when needed and verify you have all required information first.
        Before calling a tool, do some analysis within <thinking></thinking> tags.
        Place all user-facing conversational responses in <reply></reply> XML tags.
        """
            
        user_message = input("\nUser: ")
        messages = [{"role": "user", "content": user_message}]
        while True:
            try:
                # If the last message was from the assistant, get user input
                if messages and messages[-1]["role"] == "assistant":
                    query = input("\nUser: ").strip()
                    if query.lower() == 'quit':
                        break
                    messages.append({
                        "role": "user",
                        "content":  query
                    })
                else:


                    # Get response from Claude
                    response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        system=system_prompt,
                        max_tokens=1000,
                        messages=messages,
                        tools=self.available_tools
                    )

                    # Handle response content
                    for content in response.content:
                        if content.type == 'text':
                            # reply = self.extract_reply(content.text)
                            reply = content.text
                            logger.info("\nAssistant: " + reply)
                            messages.append({
                                "role": "assistant",
                                "content": content.text
                            })
                        elif content.type == 'tool_use':
                            tool_name = content.name
                            tool_args = content.input
                            
                            # Execute tool call
                            logger.info(f"\n[Tool Call] {tool_name} with args {tool_args}")
                            result = await self.session.call_tool(tool_name, tool_args)
                            
                            # Add tool result to conversation
                            if hasattr(content, 'text') and content.text:
                                messages.append({
                                    "role": "assistant",
                                    "content": content.text
                                })
                            messages.append({
                                "role": "user",
                                "content": result.content
                            })
                            
                            # No need to break here - let the loop continue for another LLM call

            except Exception as e:
                logger.error(f"\nError: {str(e)}")
                # Optionally, could add error to messages for context
                messages.append({
                    "role": "system",
                    "content": f"Error occurred: {str(e)}. Please try again."
                })

        await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        logger.info("Usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
