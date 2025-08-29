FROM python:3.11-slim

WORKDIR /app

# 安装Git和必要工具
RUN apt-get update && apt-get install -y git

# 从GitHub克隆代码
RUN git clone https://github.com/adhikasp/mcp-reddit.git .

# 安装依赖
RUN pip install --no-cache-dir -e .

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 创建启动脚本，使用环境变量PORT
RUN echo '#!/bin/bash\n\
PORT=${PORT:-8000}\n\
echo "Starting MCP server on port $PORT"\n\
python -m mcp_reddit.reddit_fetcher --transport sse --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# 使用启动脚本
CMD ["/app/start.sh"]
