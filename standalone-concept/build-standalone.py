#!/usr/bin/env python3
"""
Build script to create a standalone Alphalete Club executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

class StandaloneBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "standalone_build"
        self.dist_dir = self.project_root / "dist"
        
    def clean_build(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning previous builds...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        self.build_dir.mkdir(exist_ok=True)
        
    def build_frontend(self):
        """Build React frontend for production"""
        print("⚛️ Building React frontend...")
        frontend_dir = self.project_root / "frontend"
        
        # Install dependencies and build
        subprocess.run(["yarn", "install"], cwd=frontend_dir, check=True)
        subprocess.run(["yarn", "build"], cwd=frontend_dir, check=True)
        
        # Copy build to standalone directory
        build_output = frontend_dir / "build"
        frontend_build = self.build_dir / "frontend_build"
        shutil.copytree(build_output, frontend_build)
        print("✅ Frontend built successfully")
        
    def prepare_backend(self):
        """Prepare backend for standalone distribution"""
        print("🐍 Preparing FastAPI backend...")
        backend_dir = self.project_root / "backend"
        standalone_backend = self.build_dir / "backend"
        
        # Copy backend files
        shutil.copytree(backend_dir, standalone_backend)
        
        # Create standalone server with embedded database
        standalone_server = standalone_backend / "standalone_server.py"
        self.create_standalone_server(standalone_server)
        print("✅ Backend prepared successfully")
        
    def create_standalone_server(self, server_path):
        """Create a standalone server with embedded SQLite"""
        server_code = '''
import os
import sys
import sqlite3
import threading
import webbrowser
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

class StandaloneAlphaleteServer:
    def __init__(self):
        self.app = FastAPI(title="Alphalete Club Standalone")
        self.db_path = Path.home() / ".alphalete" / "alphalete.db"
        self.frontend_dir = Path(__file__).parent / "frontend_build"
        self.setup_database()
        self.setup_routes()
        
    def setup_database(self):
        """Initialize SQLite database"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                membership_type TEXT,
                monthly_fee REAL,
                start_date TEXT,
                next_payment_date TEXT,
                payment_status TEXT,
                amount_owed REAL,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_records (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                amount_paid REAL NOT NULL,
                payment_date TEXT NOT NULL,
                payment_method TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {self.db_path}")
        
    def setup_routes(self):
        """Setup API routes and static file serving"""
        
        # Import and setup existing API routes
        from server import api_router
        self.app.include_router(api_router, prefix="/api")
        
        # Serve React frontend
        if self.frontend_dir.exists():
            self.app.mount("/static", StaticFiles(directory=self.frontend_dir / "static"), name="static")
            
            @self.app.get("/")
            @self.app.get("/{full_path:path}")
            async def serve_react_app(request: Request):
                return FileResponse(self.frontend_dir / "index.html")
        
    def start(self, port=8080):
        """Start the standalone server"""
        print(f"🚀 Starting Alphalete Club Standalone on http://localhost:{port}")
        print("📊 Access your gym management system in your web browser")
        
        # Open browser automatically
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
        
        uvicorn.run(self.app, host="127.0.0.1", port=port)

if __name__ == "__main__":
    server = StandaloneAlphaleteServer()
    server.start()
'''
        with open(server_path, 'w') as f:
            f.write(server_code)
            
    def create_executable(self):
        """Create executable using PyInstaller"""
        print("📦 Creating standalone executable...")
        
        # Create PyInstaller spec
        spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis([
    '{self.build_dir / "backend" / "standalone_server.py"}',
],
pathex=['{self.build_dir}'],
binaries=[],
datas=[
    ('{self.build_dir / "frontend_build"}', 'frontend_build'),
    ('{self.build_dir / "backend"}', 'backend'),
],
hiddenimports=[
    'fastapi',
    'uvicorn',
    'sqlite3',
    'webbrowser',
    'threading'
],
hookspath=[],
runtime_hooks=[],
excludes=[],
win_no_prefer_redirects=False,
win_private_assemblies=False,
cipher=block_cipher,
noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AlphaleteClub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{self.project_root / "frontend" / "public" / "icon-512x512.png"}'
)
'''
        
        spec_file = self.build_dir / "alphalete.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
            
        # Run PyInstaller
        subprocess.run([
            "pyinstaller", 
            "--clean",
            "--noconfirm",
            str(spec_file)
        ], cwd=self.build_dir, check=True)
        
        print("✅ Executable created successfully")
        print(f"📍 Location: {self.build_dir / 'dist' / 'AlphaleteClub'}")
        
    def build(self):
        """Execute complete build process"""
        print("🏗️ Building Alphalete Club Standalone...")
        
        try:
            self.clean_build()
            self.build_frontend()
            self.prepare_backend()
            self.create_executable()
            
            print("\n🎉 Standalone build completed successfully!")
            print("\n📋 DISTRIBUTION:")
            print(f"   Executable: {self.build_dir / 'dist' / 'AlphaleteClub'}")
            print(f"   Size: ~50MB (includes Python runtime + React app)")
            print(f"   Database: Stored in user home directory")
            print("\n💡 USAGE:")
            print("   1. Run the executable")
            print("   2. Browser opens automatically to http://localhost:8080")
            print("   3. Fully functional gym management system")
            print("   4. No internet connection required")
            
        except Exception as e:
            print(f"❌ Build failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    builder = StandaloneBuilder()
    builder.build()