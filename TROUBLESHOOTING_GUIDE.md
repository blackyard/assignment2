# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the Agentic Codebase Genius system.

## 🔍 Quick Diagnosis

### System Health Check

Run this comprehensive diagnostic script:

```powershell
# Create diagnostic script
@"
# PowerShell Diagnostic Script
Write-Host "=== Agentic Codebase Genius Diagnostics ===" -ForegroundColor Cyan

# Check Python environment
Write-Host "`n1. Python Environment:" -ForegroundColor Yellow
python --version
python -c "import sys; print(f'Python path: {sys.executable}')"

# Check key dependencies
Write-Host "`n2. Dependencies:" -ForegroundColor Yellow
$deps = @('fastapi', 'uvicorn', 'streamlit', 'git', 'google.generativeai', 'tree_sitter')
foreach ($dep in $deps) {
    try {
        python -c "import $dep" 2>$null
        Write-Host "✓ $dep" -ForegroundColor Green
    } catch {
        Write-Host "✗ $dep" -ForegroundColor Red
    }
}

# Check services
Write-Host "`n3. Service Status:" -ForegroundColor Yellow
$ports = @(8000, 8502)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "✓ Port $port is listening (PID: $($connection.OwningProcess))" -ForegroundColor Green
    } else {
        Write-Host "✗ Port $port is not listening" -ForegroundColor Red
    }
}

# Check file permissions
Write-Host "`n4. File Permissions:" -ForegroundColor Yellow
$paths = @('backend', 'frontend', 'py_modules', 'outputs')
foreach ($path in $paths) {
    if (Test-Path $path) {
        Write-Host "✓ $path exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $path missing" -ForegroundColor Red
    }
}

# Check environment variables
Write-Host "`n5. Environment Variables:" -ForegroundColor Yellow
if ($env:GEMINI_API_KEY) {
    Write-Host "✓ GEMINI_API_KEY is set" -ForegroundColor Green
} else {
    Write-Host "✗ GEMINI_API_KEY not set" -ForegroundColor Red
}

Write-Host "`n=== Diagnostics Complete ===" -ForegroundColor Cyan
"@ | Out-File -FilePath "diagnose.ps1" -Encoding UTF8

# Run diagnostics
.\diagnose.ps1
```

## 🚨 Common Issues and Solutions

### Issue 1: "ModuleNotFoundError" on Import

**Symptoms**:
```
ModuleNotFoundError: No module named 'ccg_api'
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions**:

1. **Check Python Path**:
```powershell
# Verify PYTHONPATH includes py_modules
$env:PYTHONPATH
# Should include: C:\path\to\project\py_modules

# Set if missing
$env:PYTHONPATH = "$env:PYTHONPATH;C:\path\to\project\py_modules"
```

2. **Reinstall Dependencies**:
```powershell
# Activate environment
jac-env\Scripts\activate

# Force reinstall
pip install --force-reinstall -r requirements.txt

# Clear pip cache if needed
pip cache purge
```

3. **Check Virtual Environment**:
```powershell
# Verify correct Python is being used
which python
# Should point to: jac-env\Scripts\python.exe

# If not, activate environment
jac-env\Scripts\activate
```

### Issue 2: JAC Compilation Errors

**Symptoms**:
```
Error: Failed to compile JAC file
SyntaxError in supervisor_core.jac
```

**Solutions**:

1. **Check JAC Syntax**:
```powershell
# Test compilation
jac-env\Scripts\jac.exe build backend\supervisor_core.jac

# Check for syntax errors
jac-env\Scripts\jac.exe check backend\supervisor_core.jac
```

2. **Verify Python Path for JAC**:
```powershell
# JAC needs PYTHONPATH to find Python modules
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\py_modules"
jac-env\Scripts\jac.exe build backend\supervisor_core.jac
```

3. **Check JAC Version**:
```powershell
# Verify JAC installation
jac-env\Scripts\jac.exe --version

# Reinstall JAC if needed
pip install --upgrade jaseci
```

### Issue 3: Backend Server Won't Start

**Symptoms**:
```
Error: Port 8000 already in use
Connection refused on localhost:8000
```

**Solutions**:

1. **Kill Existing Process**:
```powershell
# Find process using port 8000
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object OwningProcess

# Kill the process
Stop-Process -Id <PID> -Force
```

2. **Use Different Port**:
```powershell
# Start on different port
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8001
```

3. **Check Firewall**:
```powershell
# Check Windows Firewall rules
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*python*" -or $_.DisplayName -like "*jac*" }
```

### Issue 4: Frontend (Streamlit) Issues

**Symptoms**:
```
Streamlit connection refused
Port 8502 not accessible
```

**Solutions**:

1. **Start Frontend Correctly**:
```powershell
# Activate environment first
jac-env\Scripts\activate

# Start with proper arguments
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true
```

2. **Check Backend Connectivity**:
```powershell
# Test backend from frontend
curl http://localhost:8000/walker/workflow_status.workflow_status
```

3. **Browser Issues**:
- Clear browser cache
- Try incognito mode
- Check browser console for JavaScript errors

### Issue 5: Repository Cloning Failures

**Symptoms**:
```
Git clone failed
Authentication error
Repository not found
```

**Solutions**:

1. **Check Git Configuration**:
```powershell
# Verify Git setup
git --version
git config --global user.name
git config --global user.email
```

2. **Test Repository Access**:
```powershell
# Test basic Git access
git ls-remote https://github.com/microsoft/vscode.git

# Test with authentication if private repo
git clone https://username:token@github.com/user/repo.git
```

3. **Check Network/Firewall**:
```powershell
# Test internet connectivity
Test-NetConnection github.com -Port 443
```

4. **Clean Cache**:
```powershell
# Clear repository cache
Remove-Item outputs\cache -Recurse -Force
```

### Issue 6: AI Service Errors

**Symptoms**:
```
Gemini API error
Rate limit exceeded
Invalid API key
```

**Solutions**:

1. **Verify API Key**:
```powershell
# Check environment variable
$env:GEMINI_API_KEY

# Test API key validity
python -c "
import google.generativeai as genai
genai.configure(api_key='$env:GEMINI_API_KEY')
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content('test')
    print('API key is valid')
except Exception as e:
    print(f'API key error: {e}')
"
```

2. **Check Rate Limits**:
- Gemini has rate limits per minute/hour
- Wait and retry, or upgrade API plan
- Implement exponential backoff in code

3. **Network Issues**:
```powershell
# Test connectivity to Google AI
Test-NetConnection generativelanguage.googleapis.com -Port 443
```

### Issue 7: Memory/Performance Issues

**Symptoms**:
```
Out of memory error
Analysis taking too long
System freezing
```

**Solutions**:

1. **Increase Memory Limits**:
```python
# In py_modules/parser.py
MAX_FILE_SIZE = 256 * 1024  # Reduce from 1MB to 256KB
```

2. **Adjust Timeouts**:
```jac
// In supervisor_core.jac
const ANALYSIS_TIMEOUT = 180;  // Reduce from 300 to 180 seconds
const CLONE_TIMEOUT = 60;     // Reduce from 180 to 60 seconds
```

3. **Process Large Repos in Batches**:
```python
# Modify clone_worker.py to limit depth
depth = 1  # Only clone top level
```

4. **Monitor Resource Usage**:
```powershell
# Check memory usage
Get-Process | Where-Object { $_.Name -like "*python*" } | Select-Object Name, Id, WorkingSet

# Check CPU usage
Get-Process | Where-Object { $_.Name -like "*python*" } | Select-Object Name, CPU
```

### Issue 8: File Permission Errors

**Symptoms**:
```
Permission denied
Cannot write to outputs/
Cannot create directory
```

**Solutions**:

1. **Check Directory Permissions**:
```powershell
# Check permissions
Get-Acl outputs | Format-List

# Fix permissions (run as Administrator)
icacls outputs /grant "Users:(OI)(CI)F" /T
```

2. **Run as Administrator**:
- Right-click PowerShell/VS Code
- "Run as Administrator"

3. **Check Antivirus**:
- Temporarily disable Windows Defender
- Add project folder to exclusions

### Issue 9: Tree-sitter Parsing Errors

**Symptoms**:
```
Tree-sitter language not found
Parsing failed for [language]
```

**Solutions**:

1. **Install Language Grammars**:
```powershell
# Install tree-sitter CLI
npm install -g tree-sitter-cli

# Clone required grammars
mkdir grammars
cd grammars
git clone https://github.com/tree-sitter/tree-sitter-python.git
git clone https://github.com/tree-sitter/tree-sitter-javascript.git
git clone https://github.com/tree-sitter/tree-sitter-java.git
```

2. **Build Language Library**:
```python
# Run in Python
from tree_sitter import Language
Language.build_library(
    'build/my-languages.so',
    [
        'grammars/tree-sitter-python',
        'grammars/tree-sitter-javascript',
        'grammars/tree-sitter-java'
    ]
)
```

3. **Disable Tree-sitter** (Fallback):
```python
# In py_modules/parser.py - comment out tree-sitter usage
# Use basic regex parsing instead
```

## 🛠️ Advanced Troubleshooting

### Debug Mode

Enable verbose logging:

```powershell
# Backend debug mode
$env:JAC_DEBUG = "true"
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000 --verbose

# Frontend debug mode
jac-env\Scripts\python.exe -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import streamlit as st
# ... rest of app.py
"
```

### Log Analysis

**Backend Logs**:
```powershell
# Capture backend output
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000 > backend.log 2>&1
```

**Frontend Logs**:
```powershell
# Streamlit logs location
# Check: %USERPROFILE%\.streamlit\logs\
```

### Network Debugging

```powershell
# Test all endpoints
$endpoints = @(
    "http://localhost:8000/walker/workflow_status.workflow_status",
    "http://localhost:8000/walker/generate_docs.start",
    "http://localhost:8502"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint -TimeoutSec 10
        Write-Host "✓ $endpoint - $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "✗ $endpoint - $($_.Exception.Message)" -ForegroundColor Red
    }
}
```

### Performance Profiling

```python
# Add profiling to slow functions
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 slowest functions
        return result
    return wrapper

# Usage
@profile_function
def slow_analysis():
    # Your analysis code here
    pass
```

## 📊 System Monitoring

### Health Check Script

Create `scripts/health_check.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive health check for Agentic Codebase Genius
"""
import requests
import subprocess
import sys
import os
from pathlib import Path

def check_service(url, name):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✓ {name}: {url}")
            return True
        else:
            print(f"✗ {name}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {name}: {str(e)}")
        return False

def check_file(path, name):
    """Check if a file/directory exists"""
    if Path(path).exists():
        print(f"✓ {name}: {path}")
        return True
    else:
        print(f"✗ {name}: {path} not found")
        return False

def main():
    print("=== Agentic Codebase Genius Health Check ===\n")

    # Check files
    print("Files:")
    files_ok = all([
        check_file("backend/supervisor_core.jac", "Supervisor Core"),
        check_file("frontend/app.py", "Frontend App"),
        check_file("py_modules/ccg_api.py", "CCG API"),
        check_file("requirements.txt", "Requirements"),
        check_file("outputs", "Outputs Directory")
    ])

    # Check services
    print("\nServices:")
    services_ok = all([
        check_service("http://localhost:8000/walker/workflow_status.workflow_status", "Backend API"),
        check_service("http://localhost:8502", "Frontend UI")
    ])

    # Check dependencies
    print("\nDependencies:")
    deps_ok = True
    try:
        import fastapi, uvicorn, streamlit, git
        print("✓ Core Python dependencies")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        deps_ok = False

    # Overall status
    print(f"\nOverall Status: {'✓ All systems operational' if all([files_ok, services_ok, deps_ok]) else '✗ Issues detected'}")

if __name__ == "__main__":
    main()
```

**Run health check**:
```powershell
jac-env\Scripts\python.exe scripts\health_check.py
```

## 🚑 Emergency Recovery

### Complete System Reset

When all else fails:

```powershell
# Stop all services
Get-Process | Where-Object { $_.Name -like "*python*" -or $_.Name -like "*jac*" } | Stop-Process -Force

# Clean environment
Remove-Item jac-env -Recurse -Force
Remove-Item outputs -Recurse -Force

# Reinitialize
python -m venv jac-env
jac-env\Scripts\activate
pip install -r requirements.txt

# Test compilation
jac-env\Scripts\jac.exe build backend\supervisor_core.jac

# Start services
jac-env\Scripts\jac.exe serve backend\supervisor_core.jac --host 127.0.0.1 --port 8000
# In another terminal:
jac-env\Scripts\python.exe -m streamlit run frontend\app.py --server.port 8502 --server.headless true
```

### Data Recovery

If you need to preserve existing data:

```powershell
# Backup important data
Copy-Item outputs\jobs.json backup_jobs.json -Force
Copy-Item outputs\progress backup_progress -Recurse -Force

# After reset, restore
Copy-Item backup_jobs.json outputs\jobs.json -Force
Copy-Item backup_progress outputs\progress -Recurse -Force
```

**Troubleshooting Guide generated by Agentic Codebase Genius**</content>
