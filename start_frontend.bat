@echo off
echo ⚛️ Starting Video Art Masterpiece Frontend...
echo.

REM Check if node_modules exists
cd frontend
if not exist node_modules (
    echo ❌ Dependencies not found! Installing...
    
    REM Try yarn first, then npm
    yarn --version >nul 2>&1
    if errorlevel 1 (
        npm install
    ) else (
        yarn install
    )
    
    if errorlevel 1 (
        echo ❌ Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Start frontend server
echo 🎨 Starting React development server on http://localhost:3000...

REM Try yarn first, then npm
yarn --version >nul 2>&1
if errorlevel 1 (
    npm start
) else (
    yarn start
)

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo ❌ Frontend failed to start. Check the error messages above.
    pause
)