# Contributing to Wikipedia MCP Server

Thank you for your interest in contributing to the Wikipedia MCP Server! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/rudra-ravi/wikipedia-mcp.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `python -m pytest`
6. Commit your changes: `git commit -m "Add your commit message"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Include type hints where appropriate

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Add integration tests for complex features

## Documentation

- Update README.md if adding new features
- Add docstrings to new functions/classes
- Update example prompts if relevant

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the requirements.txt if adding new dependencies
3. The PR will be merged once you have the sign-off of a maintainer

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## Questions?

Feel free to reach out to the maintainers or open an issue for any questions.