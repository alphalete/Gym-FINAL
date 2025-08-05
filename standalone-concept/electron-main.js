// Electron main process for standalone desktop app
const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const sqlite3 = require('sqlite3');

class AlphaleteStandaloneApp {
  constructor() {
    this.mainWindow = null;
    this.backendProcess = null;
    this.db = null;
  }

  async initializeDatabase() {
    // Use SQLite for embedded database instead of MongoDB
    const dbPath = path.join(app.getPath('userData'), 'alphalete.db');
    this.db = new sqlite3.Database(dbPath);
    
    // Create tables
    await this.createTables();
    console.log('✅ Embedded SQLite database initialized');
  }

  async createTables() {
    return new Promise((resolve, reject) => {
      this.db.serialize(() => {
        // Clients table
        this.db.run(`
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
        `);

        // Payment records table
        this.db.run(`
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
        `);

        // Settings table
        this.db.run(`
          CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
          )
        `, (err) => {
          if (err) reject(err);
          else resolve();
        });
      });
    });
  }

  async startBackend() {
    // Start embedded FastAPI server
    const pythonPath = path.join(__dirname, 'python-embedded', 'python.exe');
    const serverScript = path.join(__dirname, 'backend', 'standalone_server.py');
    
    this.backendProcess = spawn(pythonPath, [serverScript], {
      env: { 
        ...process.env,
        STANDALONE_MODE: 'true',
        DB_PATH: path.join(app.getPath('userData'), 'alphalete.db')
      }
    });

    console.log('✅ Embedded FastAPI backend started');
  }

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: true
      },
      icon: path.join(__dirname, 'assets', 'icon.png'),
      title: 'Alphalete Club - Gym Management'
    });

    // Load the React app
    this.mainWindow.loadURL('http://localhost:3000');
    
    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
      this.shutdown();
    });
  }

  async initialize() {
    await this.initializeDatabase();
    await this.startBackend();
    this.createWindow();
  }

  shutdown() {
    if (this.backendProcess) {
      this.backendProcess.kill();
    }
    if (this.db) {
      this.db.close();
    }
  }
}

// App lifecycle
app.whenReady().then(() => {
  const alphaleteApp = new AlphaleteStandaloneApp();
  alphaleteApp.initialize();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    const alphaleteApp = new AlphaleteStandaloneApp();
    alphaleteApp.initialize();
  }
});