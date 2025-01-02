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
from rich import print
logger.configure(handlers=[{"sink": RichHandler(markup=True),
                         "format": "[red]{function}[/red] {message}"}])
from typing import Optional, List, Dict, Any

class CustomerDBClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self, server_path: str):
        """Connect to the MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=[server_path]
        )
        
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"\nConnected to server with tools: {[tool for tool in tools]}")
    

    
    async def read_all_resources(self):
        """Read and display all available resources"""
        print("\n=== Reading All Resources ===")
        response = await self.session.list_resources()
         
        for resource in response.resources:
            print(f"\nResource: {resource.uri}")
            response = await self.session.read_resource(resource.uri)
            # import pdb;pdb.set_trace()
            print(response.contents[0].text)
    
    async def test_get_user(self, key: str, value: str):
        """Test the get_user tool"""
        print(f"\n=== Testing get_user (key: {key}, value: {value}) ===")
        result = await self.session.call_tool(
            "get_user",
            {"key": key, "value": value}
        )
        # import pdb;pdb.set_trace()
        print(result.content[0].text)
    
    async def test_get_order(self, order_id: str):
        """Test the get_order_by_id tool"""
        print(f"\n=== Testing get_order_by_id (order: {order_id}) ===")
        # import pdb;pdb.set_trace()
        result = await self.session.call_tool(
            name="get_order_by_id",
            arguments={"order_id": str(order_id)}  # Ensure order_id is a string
        )
        print(result.content[0].text)

    
    async def test_get_customer_orders(self, customer_id: str):
        """Test the get_customer_orders tool"""
        print(f"\n=== Testing get_customer_orders (customer: {customer_id}) ===")
        result = await self.session.call_tool(
            "get_customer_orders",
            {"customer_id": customer_id}
        )
        print(result.content[0].text)
    
    async def test_cancel_order(self, order_id: str):
        """Test the cancel_order tool"""
        print(f"\n=== Testing cancel_order (order: {order_id}) ===")
        result = await self.session.call_tool(
            "cancel_order",
            {"order_id": order_id}
        )
        print(result.content[0].text)

    async def close(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    # Create client instance
    client = CustomerDBClient()
    SERVER_PATH='./multi_tools_server.py'
    try:
        # Connect to server (update path as needed)
        await client.connect(SERVER_PATH)
        
        # Test reading resources
        await client.read_all_resources()
        
        # Test user lookups with different keys
        await client.test_get_user("email", "john@gmail.com")
        await client.test_get_user("phone", "987-654-3210")
        await client.test_get_user("username", "hiroshin")
        await client.test_get_user("email", "nonexistent@email.com")
        
        # Test order lookups
        await client.test_get_order(order_id="24601")  # Existing order
        await client.test_get_order(order_id="99999")  # Non-existent order
                
        
        # Test customer orders lookup
        await client.test_get_customer_orders("1213210")  # Customer with multiple orders
        await client.test_get_customer_orders("9999999")  # Non-existent customer
        
        # Test order cancellation
        await client.test_cancel_order("13579")  # Processing order that can be cancelled
        await client.test_cancel_order("24601")  # Shipped order that can't be cancelled
        await client.test_cancel_order("99999")  # Non-existent order
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
    finally:
        print("Ending and closing now.....")
        await client.close()
if __name__ == "__main__":
    asyncio.run(main())