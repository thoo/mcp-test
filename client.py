import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich import print

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python", # Executable
    args=["server.py"], # Optional command line arguments
    env=None # Optional environment variables
)

async def test_mcp_endpoints():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            list_tools=await session.list_tools()
            print(f"list of resources : {list_tools}")
            print('=======================================================================================')
            # Test resource endpoint
            resource_result = await session.read_resource("echo://Hello_World")
            print(f"Resource result: {resource_result}")
            print('=======================================================================================')
            
            # Test tool endpoint
            tool_result = await session.call_tool("echo_tool", arguments={"message":"Hello from tool"})
            print(f"Tool result: {tool_result}")
            print('=======================================================================================')
            print('=======================================================================================')
            print(f"Tool result: {tool_result.content[0].text}")
            print('=======================================================================================')
            
            # Test prompt endpoint
            prompt_result = await session.get_prompt("echo_prompt", arguments={"message":"Hello from prompt"})
            print(f"Prompt result: {prompt_result.messages[0].content.text}")

if __name__ == "__main__":
    asyncio.run(test_mcp_endpoints())