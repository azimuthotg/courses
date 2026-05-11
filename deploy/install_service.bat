@echo off
setlocal

set SERVICE_NAME=NPUCoursesLMS
set BASE_DIR=%~dp0..
set PYTHON_EXE=%BASE_DIR%\venv\Scripts\python.exe
set APP_ENTRY=%BASE_DIR%\deploy\waitress_serve.py
set NSSM_EXE=nssm

where %NSSM_EXE% >nul 2>nul
if errorlevel 1 (
    echo NSSM was not found in PATH. Install NSSM or add nssm.exe to PATH first.
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo Python virtual environment was not found: %PYTHON_EXE%
    exit /b 1
)

%NSSM_EXE% install %SERVICE_NAME% "%PYTHON_EXE%" "%APP_ENTRY%"
%NSSM_EXE% set %SERVICE_NAME% AppDirectory "%BASE_DIR%"
%NSSM_EXE% set %SERVICE_NAME% DisplayName "NPU Courses LMS"
%NSSM_EXE% set %SERVICE_NAME% Description "Micro-LMS Waitress service for /courses"
%NSSM_EXE% set %SERVICE_NAME% AppStdout "%BASE_DIR%\logs\waitress.out.log"
%NSSM_EXE% set %SERVICE_NAME% AppStderr "%BASE_DIR%\logs\waitress.err.log"
%NSSM_EXE% set %SERVICE_NAME% AppRotateFiles 1
%NSSM_EXE% set %SERVICE_NAME% AppRotateOnline 1
%NSSM_EXE% set %SERVICE_NAME% AppRotateBytes 10485760
%NSSM_EXE% set %SERVICE_NAME% Start SERVICE_AUTO_START

echo Service installed: %SERVICE_NAME%
echo Start it with: nssm start %SERVICE_NAME%

endlocal
