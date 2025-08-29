# import asyncio
# import os
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from mcp_use import MCPAgent, MCPClient

# async def main():
#     # Load environment variables
#     load_dotenv()
#     print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

#     # Create configuration dictionary
#     # config = {
#     #   "mcpServers": {
#     #     "playwright": {
#     #       "command": "npx",
#     #       "args": ["@playwright/mcp@latest"],
#     #       "env": {
#     #         "DISPLAY": ":1"
#     #       }
#     #     }
#     #   }
#     # }
#     config = {
#       "mcpServers": {
#           "medcalc": {
#               "command": "uv",
#               "args": [
#                   "--directory",
#                   "C:\\Users\\SNUH_VitalLab_LEGION\\Downloads\\medcalc\\medcalc",
#                   "run",
#                   "__main__.py"
#               ]
#           }
#       }
#     }
#     # Create MCPClient from configuration dictionary
#     client = MCPClient.from_dict(config)

#     # Create LLM
#     llm = ChatOpenAI(model="gpt-4o")

#     # Create agent with the client
#     agent = MCPAgent(llm=llm, client=client, max_steps=30)

#     # Run the query
#     result = await agent.run(
#         "what is the eGFR value for 64 y/o male patient with 1.5mg/dL creatine concentration? use CKD-EPI 2021"
#     )
#     print(f"\nResult: {result}")

# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("Agent Example")

@fast.agent(
  instruction="Given an object, respond only with an estimate of its size."
)
async def main():
  async with fast.run() as agent:
    await agent.interactive()

if __name__ == "__main__":
    asyncio.run(main())
