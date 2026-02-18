#!/bin/bash
# Script to move Rust crates from root to rust-future/ directory
# Run this once to organize the Rust optimization code

set -e

echo "Moving Rust crates to rust-future/ directory..."

# Move the three Rust crates
if [ -d "../watcher_embedding" ]; then
    echo "Moving watcher_embedding..."
    mv ../watcher_embedding ./ || echo "Already moved or does not exist"
else
    echo "watcher_embedding already in place or doesn't exist"
fi

if [ -d "../watcher_constraints" ]; then
    echo "Moving watcher_constraints..."
    mv ../watcher_constraints ./ || echo "Already moved or does not exist"
else
    echo "watcher_constraints already in place or doesn't exist"
fi

if [ -d "../watcher_drift" ]; then
    echo "Moving watcher_drift..."
    mv ../watcher_drift ./ || echo "Already moved or does not exist"
else
    echo "watcher_drift already in place or doesn't exist"
fi

echo ""
echo "✅ Rust crates organized in rust-future/ directory"
echo ""
echo "Next steps:"
echo "1. Read README.md (orientation)"
echo "2. Read OVERVIEW.md (when to build)"
echo "3. Read IMPLEMENTATION.md (how to build)"
echo "4. Keep REFERENCE.md handy for quick lookup"
echo ""
echo "Current state: Python MVP ships Feb 22. Rust is optional Phase 2."
