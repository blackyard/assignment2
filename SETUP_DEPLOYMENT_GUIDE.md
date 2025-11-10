# Setup and Deployment Guide

This guide provides comprehensive instructions for setting up, deploying, and maintaining the Agentic Codebase Genius (ACG) system.

## 🎯 Quick Start

### Prerequisites Check

**Required Software**:
- Windows PowerShell 5.1+ (or Windows Terminal)
- Python 3.8 or higher
- Git for Windows
- VS Code (recommended, with JAC extension)

**System Requirements**:
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Disk Space**: 5GB+ free space for repositories and cache
- **Network**: Stable internet connection for GitHub API and AI services

### One-Command Setup

```powershell
# Clone repository
git clone https://github.com/your-org/agentic-codebase-genius.git
cd agentic-codebase-genius

# Setup Python environment
python -m venv jac-env
jac-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start services
# Terminal 1: Backend
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)\py_modules"
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true
```

**Access URLs**:
- **Backend API**: http://127.0.0.1:8000
- **Web Interface**: http://localhost:8502

## 📋 Detailed Installation

### Step 1: Environment Setup

#### Python Virtual Environment

```powershell
# Create virtual environment
python -m venv jac-env

# Activate environment
jac-env\Scripts\activate

# Verify activation
python --version  # Should show Python 3.8+
which python      # Should point to jac-env\Scripts\python.exe
```

#### Dependency Installation

```powershell
# Install Python packages
pip install -r requirements.txt

# Verify installations
python -c "import fastapi, uvicorn, streamlit, git, tree_sitter, graphviz; print('All dependencies installed')"
```

### Step 2: VS Code Configuration (Recommended)

#### Install Extensions

Required VS Code extensions:
- **Jaseci Language Support** (for .jac files)
- **Python** (Microsoft)
- **Git Graph** (recommended)

### Step 3: Tree-sitter Language Setup

**Note**: Tree-sitter setup is optional but recommended for enhanced code analysis.

```powershell
# Install tree-sitter CLI (optional)
npm install -g tree-sitter-cli

# Clone language grammars (optional)
mkdir grammars
cd grammars

# Python grammar
git clone https://github.com/tree-sitter/tree-sitter-python.git

# JavaScript/TypeScript grammar
git clone https://github.com/tree-sitter/tree-sitter-javascript.git

# Java grammar
git clone https://github.com/tree-sitter/tree-sitter-java.git

# Build language library (run once)
cd ..
python -c "
import os
from tree_sitter import Language
# Build shared library (adjust paths as needed)
# Language.build_library(
#     'build/my-languages.so',
#     [
#         'grammars/tree-sitter-python',
#         'grammars/tree-sitter-javascript',
#         'grammars/tree-sitter-java'
#     ]
# )
"
```

## 🚀 Running the Application

### Development Mode

#### Option 1: VS Code Tasks (Recommended)

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` → "Tasks: Run Task"
3. Select **Jac: Serve (PYTHONPATH)** for backend
4. In a new terminal, select **Frontend: Streamlit (8502)** for frontend

#### Option 2: Manual Terminal Commands

**Terminal 1 - Backend**:
```powershell
# Activate environment
jac-env\Scripts\activate

# Set Python path for JAC imports
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)\py_modules"

# Start JAC server
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend**:
```powershell
# Activate environment
jac-env\Scripts\activate

# Start Streamlit
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true
```

### Production Mode

#### Backend Deployment

```powershell
# Using uvicorn directly (alternative to jac serve)
jac-env\Scripts\python.exe -c "
import uvicorn
from jaseci import create_app
app = create_app('backend/supervisor_core.jac')
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

#### Frontend Deployment

```powershell
# Build for production
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true --server.address 0.0.0.0
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# AI Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Server Configuration
JAC_HOST=127.0.0.1
JAC_PORT=8000
STREAMLIT_PORT=8502

# Cache Configuration
REPO_CACHE_TIMEOUT=1800
REPO_CACHE_DEPTH=1

# Analysis Configuration
MAX_FILE_SIZE=1048576  # 1MB
ANALYSIS_TIMEOUT=300   # 5 minutes
```

### JAC Configuration

Modify `backend/supervisor_core.jac` for custom settings:

```jac
# Adjust AI model
glob llm: Model = Model(model_name='gemini/gemini-2.0-flash', verbose=True);

# Configure timeouts
const CLONE_TIMEOUT = 180;  # seconds
const ANALYSIS_TIMEOUT = 300;  # seconds
```

### Streamlit Configuration

Create `frontend/.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8502
address = "127.0.0.1"

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

## 📊 Monitoring and Troubleshooting

### Log Files

**Backend Logs**:
- Console output from JAC server
- Python module logs (when verbose mode enabled)

**Frontend Logs**:
- Streamlit console output
- Browser developer console

### Common Issues

#### Issue: "JAC compilation failed"
**Solution**:
```powershell
# Check JAC syntax
jac-env\Scripts\jac.exe build backend/supervisor_core.jac

# Verify Python path
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)\py_modules"
```

#### Issue: "Import errors in Python modules"
**Solution**:
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check module paths
python -c "import sys; print('\n'.join(sys.path))"
```

#### Issue: "Repository cloning fails"
**Solution**:
```powershell
# Check Git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Test Git access
git ls-remote https://github.com/microsoft/vscode.git
```

#### Issue: "AI service unavailable"
**Solution**:
```powershell
# Check API key
echo $env:GEMINI_API_KEY

# Test AI connectivity
python -c "
import google.generativeai as genai
genai.configure(api_key='your-key')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Hello')
print(response.text)
"
```

### Performance Tuning

#### Memory Optimization

```python
# In py_modules/parser.py - reduce max file size
MAX_FILE_SIZE = 512 * 1024  # 512KB

# In py_modules/clone_worker.py - adjust clone depth
depth = 1  # Shallow clone only
```

#### Timeout Configuration

```jac
// In supervisor_core.jac
const CLONE_TIMEOUT = 120;    // 2 minutes
const ANALYSIS_TIMEOUT = 180; // 3 minutes
```

## 🚀 Deployment Options

### Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create outputs directory
RUN mkdir -p outputs

# Expose ports
EXPOSE 8000 8502

# Start both services
CMD ["python", "scripts/start_services.py"]
```

**Build and run**:
```bash
docker build -t acg .
docker run -p 8000:8000 -p 8502:8502 acg
```

### Cloud Deployment

#### Azure App Service

1. Create Web App with Python runtime
2. Configure environment variables
3. Deploy code via Git or ZIP
4. Configure custom startup command

#### AWS EC2

```bash
# Provision EC2 instance
aws ec2 run-instances --image-id ami-12345678 --instance-type t3.medium

# Install dependencies
sudo yum update -y
sudo yum install python3 git -y

# Deploy application
git clone <repository>
cd agentic-codebase-genius
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Google Cloud Run

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: acg-backend
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project-id/acg:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-key
              key: api-key
```

## 🔄 Maintenance

### Regular Tasks

#### Update Dependencies

```powershell
# Monthly dependency updates
pip list --outdated
pip install --upgrade -r requirements.txt
```

#### Clean Cache

```powershell
# Clear repository cache periodically
Remove-Item outputs\cache -Recurse -Force
Remove-Item outputs\progress -Recurse -Force
```

#### Database Maintenance

```powershell
# Clean old job records (optional)
# Edit outputs/jobs.json manually or create cleanup script
```

### Backup Strategy

**Important Files to Backup**:
- `outputs/jobs.json` - Job history
- `outputs/progress/` - Progress snapshots
- Generated documentation in `outputs/*/`
- Configuration files

**Backup Script**:
```powershell
# PowerShell backup script
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backups\$timestamp"

New-Item -ItemType Directory -Path $backupDir -Force
Copy-Item "outputs\*" $backupDir -Recurse
Copy-Item "*.json" $backupDir
Copy-Item "*.md" $backupDir

Compress-Archive -Path $backupDir -DestinationPath "backup_$timestamp.zip"
```

### Performance Benchmarks

**Typical Performance**:
- Small repository (< 100 files): 30-60 seconds
- Medium repository (100-500 files): 2-5 minutes
- Large repository (500+ files): 5-15 minutes

**Factors Affecting Performance**:
- Repository size and complexity
- Network connectivity
- AI service response times
- System resources (CPU, RAM)

---

**Setup Guide generated by Agentic Codebase Genius**</content>
