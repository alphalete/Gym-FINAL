#!/bin/bash
# Deployment script for standalone application
# This application uses in-memory storage only

export STANDALONE_APPLICATION=true
export MEMORY_STORAGE=true
export NO_EXTERNAL_DEPS=true

echo "✅ Standalone application mode"
echo "📱 Ready for deployment"
echo "🚀 Self-contained with mock data"