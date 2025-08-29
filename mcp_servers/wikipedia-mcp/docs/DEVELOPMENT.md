# Development Guide

This guide provides information for developers who want to contribute to the Wikipedia MCP server.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/rudra-ravi/wikipedia-mcp.git
cd wikipedia-mcp
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Project Structure

```
wikipedia-mcp/
├── docs/                    # Documentation
├── examples/                # Example scripts
├── tests/                   # Test files
├── wikipedia_mcp/          # Main package
│   ├── api/                # API endpoints
│   ├── utils/              # Utility functions
│   ├── __init__.py
│   ├── __main__.py         # Entry point
│   ├── server.py           # Server implementation
│   └── wikipedia_client.py # Wikipedia API client
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run tests with coverage:
```bash
python -m pytest --cov=wikipedia_mcp tests/
```

## Code Style

This project follows PEP 8 style guidelines. Use `black` for code formatting and `flake8` for linting:

```bash
# Format code
black .

# Run linter
flake8 .
```

## Making Changes

1. Create a new branch for your changes:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and write tests if necessary

3. Run the test suite to ensure everything works:
```bash
python -m pytest
```

4. Commit your changes:
```bash
git add .
git commit -m "Description of your changes"
```

5. Push to your fork and create a pull request

## Building Documentation

The documentation is written in Markdown and can be found in the `docs/` directory:

- `API.md` - API documentation
- `DEVELOPMENT.md` - Development guide (this file)

## Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create a new release on GitHub
4. Build and upload to PyPI:
```bash
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Environment Variables

The following environment variables can be set in a `.env` file:

- `WIKIPEDIA_LANGUAGE` - Language code for Wikipedia API (default: "en")
- `LOG_LEVEL` - Logging level (default: "INFO")

## Troubleshooting

### Common Issues

1. **Import errors after installing in development mode**
   - Make sure you're in the virtual environment
   - Try reinstalling the package: `pip install -e .`

2. **Tests failing**
   - Check if all dependencies are installed
   - Make sure you're using Python 3.9 or higher
   - Try clearing the pytest cache: `pytest --cache-clear`

### Getting Help

- Open an issue on GitHub
- Check existing issues for similar problems
- Include relevant logs and error messages

## Contributing Guidelines

1. Follow the code style guidelines
2. Write tests for new features
3. Update documentation as needed
4. Keep pull requests focused on a single change
5. Add yourself to CONTRIBUTORS.md if you want

## Architecture

### Components

1. **Server (`server.py`)**
   - Handles HTTP requests
   - Registers MCP tools
   - Manages API endpoints

2. **Wikipedia Client (`wikipedia_client.py`)**
   - Interacts with Wikipedia API
   - Handles data formatting
   - Manages error handling

3. **API Layer (`api/`)**
   - Defines HTTP endpoints
   - Handles request validation
   - Manages response formatting

### Data Flow

1. Request comes in through HTTP or MCP tool
2. Server routes to appropriate handler
3. Wikipedia client fetches data
4. Response is formatted and returned

## Performance Considerations

- Use caching when appropriate
- Limit response sizes for large articles
- Handle rate limiting from Wikipedia API
- Consider implementing request pooling for high load

## Security

- Don't expose sensitive configuration
- Validate all input parameters
- Handle errors gracefully
- Follow security best practices

## Future Development

Areas for improvement:

- Add caching layer
- Implement rate limiting
- Add more Wikipedia API features
- Improve error handling
- Add more examples
- Expand test coverage
