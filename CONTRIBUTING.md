# Contributing to YouTube Downloader

Thank you for your interest in contributing to the YouTube Downloader project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Security Guidelines](#security-guidelines)
- [Pull Request Process](#pull-request-process)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing opinions and experiences
- Accept responsibility and learn from mistakes

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or inflammatory comments
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- **Git** for version control
- **yt-dlp.exe** and **ffmpeg.exe** in project root
- A code editor (VS Code, PyCharm, etc.)

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/UMD.git
   cd UMD
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate          # Windows
   # source venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure Environment**
   ```bash
   # Backend
   cd backend
   copy .env.example .env  # Windows
   # cp .env.example .env  # macOS/Linux

   # Edit .env with your settings
   ```

5. **Run Development Servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   python -m app.main

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

---

## Development Workflow

### 1. Create a Branch

Always create a new branch for your work:

```bash
# For features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/bug-description

# For documentation
git checkout -b docs/documentation-update
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the coding standards below
- Add tests for new features
- Update documentation as needed

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Linting
cd backend
flake8 app/
black app/ --check

cd frontend
npm run lint
```

### 4. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add playlist sorting feature"
```

**Commit Message Format**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

## Coding Standards

### Python (Backend)

#### Style Guide
- Follow **PEP 8** style guide
- Use **Black** for code formatting
- Use **flake8** for linting
- Maximum line length: 88 characters (Black default)

#### Code Organization
```python
# 1. Standard library imports
import os
import sys
from typing import List, Optional

# 2. Third-party imports
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

# 3. Local application imports
from app.models.database import Download
from app.core.exceptions import DownloadError
```

#### Type Hints
Always use type hints for function parameters and return values:

```python
def process_download(url: str, download_type: str) -> Download:
    """Process a download request.

    Args:
        url: YouTube video URL
        download_type: Type of download (video or audio)

    Returns:
        Download object with processing status

    Raises:
        DownloadError: If URL is invalid or download fails
    """
    # Implementation
```

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `DownloadService`)
- **Functions/Methods**: `snake_case` (e.g., `create_download`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_QUEUE_SIZE`)
- **Private methods**: `_snake_case` (e.g., `_validate_url`)

#### Documentation
- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring format
- Include type information in docstrings

### JavaScript/React (Frontend)

#### Style Guide
- Follow **ESLint** configuration
- Use **Prettier** for code formatting
- Use ES6+ features (arrow functions, destructuring, etc.)

#### Component Structure
```javascript
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * DownloadCard component displays a single download item
 *
 * @param {Object} props - Component props
 * @param {Object} props.download - Download object
 * @param {Function} props.onCancel - Cancel callback
 */
const DownloadCard = ({ download, onCancel }) => {
  // Component logic

  return (
    // JSX
  );
};

DownloadCard.propTypes = {
  download: PropTypes.object.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default DownloadCard;
```

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `DownloadList`)
- **Functions**: `camelCase` (e.g., `handleDownload`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`)
- **Files**: Match component name (e.g., `DownloadList.jsx`)

---

## Testing Guidelines

### Backend Testing

#### Writing Tests
```python
# tests/test_download_service.py
import pytest
from app.services.download_service import DownloadService

def test_create_download_with_valid_url():
    """Test creating download with valid YouTube URL"""
    service = DownloadService()
    result = service.create_download("https://youtube.com/watch?v=test123")

    assert result.status == "queued"
    assert result.url == "https://youtube.com/watch?v=test123"

def test_create_download_with_invalid_url():
    """Test that invalid URLs raise DownloadError"""
    service = DownloadService()

    with pytest.raises(DownloadError):
        service.create_download("not-a-valid-url")
```

#### Running Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_download_service.py

# Run specific test
pytest tests/test_download_service.py::test_create_download_with_valid_url
```

### Frontend Testing

#### Component Testing
```javascript
// DownloadCard.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import DownloadCard from './DownloadCard';

describe('DownloadCard', () => {
  const mockDownload = {
    id: 1,
    title: 'Test Video',
    status: 'downloading',
    progress: 50
  };

  test('renders download information', () => {
    render(<DownloadCard download={mockDownload} />);

    expect(screen.getByText('Test Video')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  test('calls onCancel when cancel button clicked', () => {
    const mockCancel = jest.fn();
    render(<DownloadCard download={mockDownload} onCancel={mockCancel} />);

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockCancel).toHaveBeenCalledWith(1);
  });
});
```

---

## Security Guidelines

### Critical Security Requirements

When contributing code that touches security-sensitive areas:

1. **Input Validation**
   - Always validate and sanitize user input
   - Use Pydantic schemas for API validation
   - Never trust client-side validation alone

2. **Path Security**
   - Use `validate_download_path()` for file paths
   - Never allow directory traversal
   - Test with malicious paths: `../../etc/passwd`

3. **URL Security**
   - Use `sanitize_url()` for all URLs
   - Block shell metacharacters
   - Test with command injection attempts

4. **Authentication**
   - Use constant-time comparison for secrets
   - Never log sensitive information
   - Test authentication bypass scenarios

5. **Rate Limiting**
   - Respect existing rate limits
   - Add rate limiting to new endpoints
   - Test limit enforcement

### Security Testing

Before submitting security-related changes:

```bash
# Run security scanners
cd backend
bandit -r app/ -ll
safety check --file requirements.txt

cd frontend
npm audit
```

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead, email security concerns to: [your-security-email@example.com]

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

---

## Pull Request Process

### Before Submitting

1. **Update Documentation**
   - Update README.md if adding features
   - Update API documentation
   - Add docstrings to new functions

2. **Run All Tests**
   ```bash
   # Backend
   cd backend
   pytest
   flake8 app/
   black app/ --check

   # Frontend
   cd frontend
   npm test
   npm run lint
   ```

3. **Update CHANGELOG.md**
   Add your changes under `[Unreleased]` section

4. **Security Check**
   ```bash
   bandit -r backend/app/ -ll
   npm audit --audit-level=moderate
   ```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Security fix

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Security Checklist
- [ ] Input validation added
- [ ] No SQL injection risks
- [ ] No command injection risks
- [ ] Security scanners pass

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] CHANGELOG updated
- [ ] Docstrings added

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### Review Process

1. At least one maintainer must review
2. All tests must pass
3. Security checks must pass
4. Documentation must be updated
5. Conflicts must be resolved

---

## Bug Reports

### Before Submitting

1. **Search existing issues** to avoid duplicates
2. **Test on latest version** to ensure bug still exists
3. **Gather information**:
   - Operating system
   - Python version
   - Node.js version
   - Browser (for frontend issues)

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Screenshots**
If applicable

**Environment**
- OS: [e.g., Windows 10]
- Python: [e.g., 3.10.5]
- Node.js: [e.g., 18.12.0]
- Browser: [e.g., Chrome 120]

**Additional Context**
Any other relevant information
```

---

## Feature Requests

### Before Submitting

1. Check existing feature requests
2. Consider if it fits project scope
3. Think about implementation details

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature

**Problem It Solves**
What problem does this solve?

**Proposed Solution**
How would you implement it?

**Alternatives Considered**
Other solutions you've thought about

**Additional Context**
Any other relevant information
```

---

## Documentation

### Types of Documentation

1. **Code Comments**
   - Explain complex logic
   - Document workarounds
   - Add TODO/FIXME notes

2. **Docstrings**
   - All public functions
   - All classes
   - Use Google or NumPy format

3. **API Documentation**
   - Update OpenAPI/Swagger docs
   - Include examples
   - Document error responses

4. **User Documentation**
   - Update README.md
   - Add to troubleshooting section
   - Update configuration guides

### Documentation Standards

- Use clear, simple language
- Include code examples
- Add screenshots for UI features
- Keep documentation up-to-date

---

## Questions?

If you have questions about contributing:

- Open a discussion on GitHub
- Check existing documentation
- Review closed issues/PRs for examples
- Email: [your-contact-email@example.com]

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

**Thank you for contributing to YouTube Downloader!**
