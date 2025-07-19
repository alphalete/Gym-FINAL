#!/bin/bash
# Pre-deployment hook to prevent MongoDB setup
export SKIP_MONGODB_MIGRATION=true
export NO_DATABASE_SETUP=true
echo "Standalone application - no database setup required"