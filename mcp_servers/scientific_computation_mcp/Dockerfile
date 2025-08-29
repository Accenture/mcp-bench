FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_HTTP_TIMEOUT=60

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y curl


# Install uv package manager
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies using uv
RUN uv add numpy
RUN uv add "mcp[cli]"
RUN uv add sympy
RUN uv add matplotlib
RUN uv add pydantic

# Expose the port (if needed)
#EXPOSE 8000

# Start the MCP server using uv
CMD ["uv", "run", "src/server.py"]