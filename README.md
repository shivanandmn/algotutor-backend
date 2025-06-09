# MyCodeJudge Python Backend

A FastAPI-based backend for the MyCodeJudge platform.

## Features

- FastAPI-based REST API
- MongoDB with Motor and Beanie ODM
- Docker-based code execution
- OAuth2 authentication
- Comprehensive test suite
- Async operations

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

4. Run tests:
```bash
poetry run pytest
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
mycodejudge/
├── app/
│   ├── api/            # API endpoints
│   ├── core/           # Core configuration
│   ├── models/         # Database models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── tests/          # Test suite
└── docker/            # Docker configurations
```

## Contributing

1. Create a new branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

MIT


User Code -> Create Source File -> Check Language Type
                                     |
                    Interpreted     / \    Compiled
                        |         /   \      |
                        v        /     \     v
                Run Directly    /       \  Compile Code
                              /         \    |
                             /           \   |
                            v             v  v
                        Run Test Cases <- Success?
                                           |
                                           v
                                    Return Results