# eBay App Test Runner PowerShell Script
# This script calls run_tests.py to execute tests with logging

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "unit", "integration", "api", "database", "coverage", "frontend", "listing-generator", "price-generator")]
    [string]$TestType = "all",
    
    [Parameter(Mandatory=$false)]
    [string]$LogFile = "test_results.log"
)

# Create logs directory if it doesn't exist
$LogsDir = "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

# Generate timestamp for log file
$Timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$LogFile = "$LogsDir\test_$Timestamp.log"

# Function to write to both console and log file
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Level = "INFO"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    # Write to console with color coding
    switch ($Level) {
        "ERROR" { Write-Host $LogMessage -ForegroundColor Red }
        "WARNING" { Write-Host $LogMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $LogMessage -ForegroundColor Green }
        "INFO" { Write-Host $LogMessage -ForegroundColor Cyan }
        default { Write-Host $LogMessage }
    }
    
    # Write to log file
    Add-Content -Path $LogFile -Value $LogMessage
}

# Function to create a separator line
function Write-Separator {
    Write-Log ("=" * 80) "INFO"
}

# Function to run test command
function Invoke-TestRun {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command,
        
        [Parameter(Mandatory=$true)]
        [string]$Description
    )
    
    Write-Log "Starting: $Description" "INFO"
    Write-Log "Command: $Command" "INFO"
    
    # Create a log file for this specific test run
    $TestLogFile = "$LogsDir\$($Description -replace ' ', '_')_$Timestamp.log"
    
    try {
        # Run the command and capture output
        $CommandParts = $Command -split ' '
        $Executable = $CommandParts[0]
        $CommandArguments = @()
        if ($CommandParts.Length -gt 1) {
            $CommandArguments = $CommandParts[1..($CommandParts.Length - 1)]
        }
        & $Executable @CommandArguments 2>&1 | Tee-Object -FilePath $TestLogFile | Out-Null
        
        # Check exit code
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Completed: $Description - SUCCESS" "SUCCESS"
            return $true
        } else {
            Write-Log "Completed: $Description - FAILED (Exit Code: $LASTEXITCODE)" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error running $Description`: $_" "ERROR"
        return $false
    }
}

# Main execution
Write-Separator
Write-Log "eBay App Test Runner" "INFO"
Write-Separator
Write-Log "Test Type: $TestType" "INFO"
Write-Log "Log File: $LogFile" "INFO"
Write-Log "Timestamp: $Timestamp" "INFO"

# Check if Python is installed
try {
    $PythonVersion = .venv\Scripts\python --version 2>&1
    Write-Log "Python Version: $PythonVersion" "INFO"
    $PythonExe = ".venv\Scripts\python"
} catch {
    # Fallback to system python
    try {
        $PythonVersion = python --version 2>&1
        Write-Log "Python Version: $PythonVersion" "INFO"
        $PythonExe = "python"
    } catch {
        Write-Log "Python not found or not in PATH. Please install Python and add it to PATH." "ERROR"
        exit 1
    }
}

# Build command for run_tests.py
$Command = "run_tests.py"
switch ($TestType) {
    "unit" { $Command += " --unit" }
    "integration" { $Command += " --integration" }
    "api" { $Command += " --api" }
    "database" { $Command += " --database" }
    "coverage" { $Command += " --coverage" }
    "frontend" { $Command += " --frontend" }
    "listing-generator" { $Command += " --listing-generator" }
    "price-generator" { $Command += " --price-generator" }
}

# Run the tests using run_tests.py
$Result = Invoke-TestRun "$PythonExe $Command" "Test Suite via run_tests.py"

# Summary
Write-Log " " "INFO"
Write-Separator
Write-Log "Test Summary" "INFO"
Write-Separator

if ($Result) {
    Write-Log "Tests completed successfully!" "SUCCESS"
    Write-Log "Log files saved to: $LogsDir" "INFO"
    exit 0
} else {
    Write-Log "Tests failed. Please check the log files for details." "ERROR"
    Write-Log "Log files saved to: $LogsDir" "INFO"
    exit 1
}
