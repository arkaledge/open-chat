# Contributing to OpenChat

Thank you for your interest in contributing to OpenChat! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Prioritize the community's best interests

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, versions, etc.)
   - Screenshots if applicable

### Suggesting Features

1. Check if the feature has been suggested in Issues
2. Create a new issue with:
   - Clear use case description
   - Why this feature would be valuable
   - Proposed implementation approach
   - Any alternatives considered

### Code Contributions

#### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/openchat.git
   cd openchat
   ```

3. Create a development branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. Run the setup script:
   ```bash
   ./scripts/setup.sh
   ```

#### Making Changes

1. **Backend (Python)**:
   - Follow PEP 8 style guide
   - Add type hints to function signatures
   - Write docstrings for classes and functions
   - Add tests for new functionality
   - Run tests: `pytest`
   - Format code: `black app/`
   - Check types: `mypy app/`

2. **Frontend (TypeScript)**:
   - Follow the existing code style
   - Use TypeScript types (avoid `any`)
   - Write clean, self-documenting code
   - Add comments for complex logic
   - Run linter: `npm run lint`
   - Check types: `npm run type-check`

3. **Documentation**:
   - Update README.md if adding features
   - Add/update API documentation
   - Include code examples where appropriate

#### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for >80% code coverage
- Test edge cases and error conditions

#### Commit Messages

Follow conventional commits format:

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(chat): add streaming support for responses

Implement Server-Sent Events for streaming AI responses,
providing real-time feedback to users.

Closes #123
```

#### Pull Requests

1. Push your changes to your fork
2. Create a Pull Request with:
   - Clear title describing the change
   - Description of what changed and why
   - Link to related issues
   - Screenshots for UI changes
   - Test results if applicable

3. Wait for review:
   - Address reviewer feedback
   - Keep the PR up to date with main branch
   - Ensure CI passes

## Project Structure

```
openchat/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Configuration and security
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── main.py   # Application entry point
│   └── tests/        # Backend tests
├── frontend/         # Next.js frontend
│   ├── src/
│   │   ├── app/      # Next.js pages
│   │   ├── components/ # React components
│   │   ├── services/ # API client
│   │   ├── stores/   # State management
│   │   └── types/    # TypeScript types
│   └── tests/        # Frontend tests
├── k8s/              # Kubernetes configs
└── docs/             # Documentation
```

## Development Guidelines

### Backend

- Use async/await for I/O operations
- Implement proper error handling
- Add logging for important operations
- Use dependency injection via FastAPI
- Keep business logic in services layer
- Database queries in repository pattern

### Frontend

- Use functional components with hooks
- Implement proper loading states
- Handle errors gracefully
- Keep components small and focused
- Use TypeScript strictly
- Optimize for performance

### Database

- Use Alembic for migrations
- Never modify migrations once merged
- Include both upgrade and downgrade
- Test migrations thoroughly

### API Design

- Follow REST conventions
- Use appropriate HTTP methods
- Return consistent error formats
- Version APIs (/api/v1/)
- Document with OpenAPI

## Review Process

1. Automated checks must pass (tests, linting, type checking)
2. At least one maintainer approval required
3. Changes must be rebased on latest main
4. Squash commits before merging

## Release Process

1. Version bump in package files
2. Update CHANGELOG.md
3. Create release branch
4. Tag release
5. Build and publish Docker images

## Questions?

Feel free to ask questions by:
- Opening a discussion on GitHub
- Joining our Discord community
- Emailing maintainers

Thank you for contributing to OpenChat!
