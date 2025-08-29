import asyncio
from mcp_agent.core.fastagent import FastAgent

fast = FastAgent("fast-agent example")

@fast.agent(
  instruction="You are a helpful agent. Answer considering the token limit.",
)
async def main():
    async with fast.run() as agent:
        risk = await agent("57 y/o male smoker patient has total cholesterol density of 230mg/dL and HDL 60mg/dL. Systolic BP is 110mmHg, while having his BP controlled by medicine. What is his 10-year risk of heart attack? use Framingham Risk Score for Hard Coronary Heart Disease")
        print(f"risk: {risk}")

if __name__ == "__main__":
    asyncio.run(main())
