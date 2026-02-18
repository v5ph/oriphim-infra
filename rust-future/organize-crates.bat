@echo off
REM Script to move Rust crates from root to rust-future\ directory
REM Run this once to organize the Rust optimization code

setlocal enabledelayedexpansion

echo Moving Rust crates to rust-future\ directory...
echo.

REM Move the three Rust crates
if exist "..\watcher_embedding" (
    echo Moving watcher_embedding...
    move "..\watcher_embedding" "." >nul 2>&1 || echo Already moved or error occurred
) else (
    echo watcher_embedding already in place or doesn't exist
)

if exist "..\watcher_constraints" (
    echo Moving watcher_constraints...
    move "..\watcher_constraints" "." >nul 2>&1 || echo Already moved or error occurred
) else (
    echo watcher_constraints already in place or doesn't exist
)

if exist "..\watcher_drift" (
    echo Moving watcher_drift...
    move "..\watcher_drift" "." >nul 2>&1 || echo Already moved or error occurred
) else (
    echo watcher_drift already in place or doesn't exist
)

echo.
echo.
echo ✓ Rust crates organized in rust-future\ directory
echo.
echo Next steps:
echo 1. Read README.md (orientation)
echo 2. Read OVERVIEW.md (when to build)
echo 3. Read IMPLEMENTATION.md (how to build)
echo 4. Keep REFERENCE.md handy for quick lookup
echo.
echo Current state: Python MVP ships Feb 22. Rust is optional Phase 2.
echo.

pause
