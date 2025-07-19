#!/bin/bash
# Deployment script override
# This application does not use MongoDB or any database

export NO_MONGODB=true
export NO_DATABASE=true
export SKIP_DB_MIGRATION=true
export STANDALONE_APPLICATION=true

echo "🚫 No database setup required"
echo "✅ Standalone application mode"
echo "📱 Ready for deployment without external dependencies"