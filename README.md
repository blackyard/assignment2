# Agentic Codebase Genius (ACG)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Jaseci](https://img.shields.io/badge/Jaseci-1.0+-green.svg)](https://jaseci.org/)

**Agentic Codebase Genius** is an AI-powered system that automatically analyzes GitHub repositories and generates comprehensive documentation using advanced language models and multi-agent orchestration.

## 🌟 Features

### Core Capabilities
- **Intelligent Repository Analysis**: Deep code analysis using tree-sitter parsing for Python, JavaScript, and Java
- **AI-Powered Documentation**: Leverages Gemini 2.0 Flash for generating detailed, context-aware documentation
- **Multi-Agent Architecture**: Jaseci-based orchestration with specialized agents for different tasks
- **Progress Tracking**: Real-time progress monitoring with resumable operations
- **Caching System**: Intelligent repository caching to avoid redundant processing
- **Web Interface**: Modern Streamlit-based UI for easy interaction

### Analysis Features
- **Code Structure Mapping**: Generates repository structure diagrams and code flow analysis
- **Function Documentation**: Automatic generation of function/method descriptions with parameters and return types
- **Architecture Diagrams**: Visual representation of system architecture and component relationships
- **Dependency Analysis**: Identification of internal and external dependencies
- **Code Quality Metrics**: Basic code quality and complexity analysis

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Git**
- **Windows PowerShell** (or Windows Terminal)

### One-Command Setup

```powershell
# Clone and setup
git clone <repository-url>
cd agentic-codebase-genius

# Create environment and install
python -m venv jac-env
jac-env\Scripts\activate
pip install -r requirements.txt

# Start services
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000
# In another terminal:
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true
```

**Access the application**:
- **Web Interface**: http://localhost:8502
- **API Documentation**: http://localhost:8000/docs

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [API Reference](#-api-reference)
- [Setup Guide](./SETUP_DEPLOYMENT_GUIDE.md)
- [Troubleshooting](./TROUBLESHOOTING_GUIDE.md)
- [Contributing](#-contributing)
- [License](#-license)

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   JAC Backend   │    │   AI Services   │
│   (Streamlit)   │◄──►│  (Multi-agent)  │◄──►│   (Gemini)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Progress UI    │    │  Repository     │    │ Documentation   │
│                 │    │  Analysis       │    │  Generation     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

#### Backend (JAC)
- **`supervisor_core.jac`**: Main orchestration agent managing the documentation generation workflow
- **`doc_genie.jac`**: Specialized agent for AI-powered documentation creation
- **`code_analyzer.jac`**: Code analysis and structure mapping agent
- **`repo_mapper.jac`**: Repository structure analysis and mapping agent

#### Python Modules
- **`ccg_api.py`**: REST API endpoints and request handling
- **`docs_saver.py`**: Documentation persistence and file management
- **`parser.py`**: Multi-language code parsing using tree-sitter
- **`job_registry.py`**: Task management and progress tracking
- **`repo_cache.py`**: Intelligent repository caching system
- **`clone_worker.py`**: Git repository cloning and management

#### Frontend
- **`app.py`**: Streamlit-based web interface with real-time progress monitoring

## 📚 Documentation

### Generated Documentation Structure

When you analyze a repository, ACG generates:

```
outputs/
├── {repo-name-hash}/
│   ├── analysis.json          # Detailed code analysis
│   ├── ccg                    # Code structure data
│   ├── docs.md               # Comprehensive documentation
│   └── diagrams/             # Architecture diagrams
├── cache/                    # Repository cache
├── progress/                 # Progress snapshots
└── jobs.json                # Job registry
```

### Documentation Types

1. **Project Overview**: High-level system description and architecture
2. **Module Documentation**: Detailed API documentation for each module
3. **Code Analysis**: Function-by-function breakdown with complexity metrics
4. **Architecture Diagrams**: Visual representation of system structure
5. **Dependency Maps**: Internal and external dependency relationships

## 🔌 API Reference

### Core Endpoints

#### Generate Documentation
```http
POST /walker/generate_docs.start
Content-Type: application/json

{
  "repo_url": "https://github.com/microsoft/vscode",
  "task_id": "optional-custom-id"
}
```

#### Check Progress
```http
GET /walker/workflow_status.workflow_status
```

**Response**:
```json
{
  "jobs": [
    {
      "task_id": "abc-123",
      "status": "in_progress|completed|failed",
      "progress": 75,
      "current_step": "Analyzing code structure...",
      "repo_url": "https://github.com/microsoft/vscode"
    }
  ]
}
```

#### Get Documentation
```http
GET /walker/generate_docs.get_result?task_id=abc-123
```

### Additional Endpoints

- `POST /walker/generate_docs.cancel` - Cancel running job
- `GET /walker/repo_cache.list_cache` - List cached repositories
- `POST /walker/repo_cache.clear_cache` - Clear repository cache

## 🛠️ Development

### VS Code Setup (Recommended)

1. **Install Extensions**:
   - Jaseci Language Support
   - Python (Microsoft)
   - Git Graph

2. **Pre-configured Tasks**:
   - `Jac: Build` - Compile JAC modules
   - `Jac: Serve` - Start backend server
   - `Frontend: Streamlit` - Start web interface
   - `Smoke: Run checks` - System validation

### Testing

```powershell
# Run smoke tests
jac-env\Scripts\python.exe scripts\smoke_checks.py

# Run end-to-end tests
jac-env\Scripts\python.exe scripts\e2e_generate_docs.py

# Run linting (optional)
jac-env\Scripts\python.exe -m ruff check .
jac-env\Scripts\python.exe -m mypy py_modules/
```

### Code Quality

The project includes optional linting and type checking:

- **Ruff**: Fast Python linter
- **MyPy**: Static type checker

## 📊 Performance

### Benchmarks

- **Small Repository** (< 100 files): 30-60 seconds
- **Medium Repository** (100-500 files): 2-5 minutes
- **Large Repository** (500+ files): 5-15 minutes

### Optimization Features

- **Intelligent Caching**: Avoids re-processing unchanged repositories
- **Parallel Processing**: Concurrent analysis of multiple files
- **Memory Management**: Configurable file size limits and timeouts
- **Incremental Analysis**: Resume interrupted analysis operations

## 🔧 Configuration

### Environment Variables

```env
# Required
GEMINI_API_KEY=your-api-key-here

# Optional
JAC_HOST=127.0.0.1
JAC_PORT=8000
STREAMLIT_PORT=8502
REPO_CACHE_TIMEOUT=1800
MAX_FILE_SIZE=1048576
```

### JAC Configuration

Modify `backend/supervisor_core.jac`:

```jac
# AI Model Configuration
glob llm: Model = Model(model_name='gemini/gemini-2.0-flash', verbose=True);

# Timeout Settings
const CLONE_TIMEOUT = 180;
const ANALYSIS_TIMEOUT = 300;
```

## 🚀 Deployment

### Local Development
See [Setup Guide](./SETUP_DEPLOYMENT_GUIDE.md) for detailed instructions.

### Production Deployment

#### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8502
CMD ["python", "scripts/start_services.py"]
```

#### Cloud Platforms
- **Azure App Service**: Python runtime with custom startup
- **AWS EC2**: Manual deployment with systemd services
- **Google Cloud Run**: Containerized deployment

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes with tests
4. **Run** tests and linting: `scripts/smoke_checks.py`
5. **Commit** your changes: `git commit -m 'Add amazing feature'`
6. **Push** to the branch: `git push origin feature/amazing-feature`
7. **Open** a Pull Request

### Code Standards

- **Python**: PEP 8 with type hints
- **JAC**: Follow established patterns in existing modules
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Unit tests for critical functions

### Areas for Contribution

- **New Language Support**: Add tree-sitter parsers for additional languages
- **Enhanced AI Models**: Integration with other LLM providers
- **UI Improvements**: Better frontend design and user experience
- **Performance Optimization**: Faster analysis algorithms
- **Additional Output Formats**: PDF, HTML, or other documentation formats

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Jaseci**: For the powerful multi-agent orchestration framework
- **Google AI**: For the Gemini language models
- **Tree-sitter**: For multi-language code parsing
- **Streamlit**: For the excellent web application framework

## 📞 Support

### Getting Help

1. **Check Documentation**: See [Setup Guide](./SETUP_DEPLOYMENT_GUIDE.md) and [Troubleshooting](./TROUBLESHOOTING_GUIDE.md)
2. **Run Diagnostics**: Use the built-in health check scripts
3. **GitHub Issues**: Report bugs or request features
4. **Community**: Join discussions in GitHub Discussions

### Common Issues

- **Import Errors**: Check PYTHONPATH includes `py_modules`
- **JAC Compilation**: Ensure Python environment is activated
- **Memory Issues**: Reduce MAX_FILE_SIZE or increase system RAM
- **AI API Errors**: Verify GEMINI_API_KEY and network connectivity

---

**Built with ❤️ using Jaseci, Gemini AI, and modern Python tooling**

*Agentic Codebase Genius - Making code documentation intelligent and automatic*
