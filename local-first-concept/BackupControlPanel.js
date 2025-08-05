/**
 * Backup Control Panel Component
 * Gives users full control over their data backup
 */

import React, { useState, useEffect } from 'react';

const BackupControlPanel = ({ localFirstManager }) => {
  const [storageStatus, setStorageStatus] = useState(null);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [backupHistory, setBackupHistory] = useState([]);
  const [syncSettings, setSyncSettings] = useState({
    autoBackup: false,
    backupFrequency: 'daily',
    cloudProvider: 'none'
  });

  useEffect(() => {
    loadStorageStatus();
    loadSyncSettings();
  }, []);

  const loadStorageStatus = async () => {
    try {
      const status = await localFirstManager.getStorageStatus();
      setStorageStatus(status);
    } catch (error) {
      console.error('Error loading storage status:', error);
    }
  };

  const loadSyncSettings = async () => {
    // Load current sync settings
    setSyncSettings(localFirstManager.syncSettings);
  };

  const handleManualBackup = async () => {
    setIsBackingUp(true);
    try {
      const filename = await localFirstManager.createBackupFile();
      setBackupHistory(prev => [...prev, {
        timestamp: new Date().toISOString(),
        filename,
        type: 'manual',
        status: 'success'
      }]);
      await loadStorageStatus();
    } catch (error) {
      console.error('Backup failed:', error);
      setBackupHistory(prev => [...prev, {
        timestamp: new Date().toISOString(),
        error: error.message,
        type: 'manual',
        status: 'failed'
      }]);
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleCloudSync = async () => {
    if (syncSettings.cloudProvider === 'none') {
      alert('Please configure a cloud provider first');
      return;
    }

    setIsBackingUp(true);
    try {
      const success = await localFirstManager.syncToCloud();
      if (success) {
        setBackupHistory(prev => [...prev, {
          timestamp: new Date().toISOString(),
          type: 'cloud',
          provider: syncSettings.cloudProvider,
          status: 'success'
        }]);
        await loadStorageStatus();
      }
    } catch (error) {
      console.error('Cloud sync failed:', error);
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleRestoreFile = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const backupData = JSON.parse(e.target.result);
        const confirmed = window.confirm(
          `This will replace all current data with backup from ${backupData.timestamp}. ` +
          `Backup contains ${backupData.metadata.total_clients} clients and ` +
          `${backupData.metadata.total_payments} payments. Continue?`
        );
        
        if (confirmed) {
          await localFirstManager.restoreFromBackup(backupData);
          alert('Backup restored successfully!');
          await loadStorageStatus();
        }
      } catch (error) {
        console.error('Restore failed:', error);
        alert('Failed to restore backup: Invalid file format');
      }
    };
    reader.readAsText(file);
  };

  const updateSyncSettings = async (newSettings) => {
    const updatedSettings = { ...syncSettings, ...newSettings };
    setSyncSettings(updatedSettings);
    localFirstManager.syncSettings = updatedSettings;
    await localFirstManager.saveSyncSettings();
  };

  if (!storageStatus) {
    return <div className="loading">Loading storage status...</div>;
  }

  return (
    <div className="backup-control-panel">
      <div className="panel-header">
        <h2>📱 Local Storage & Backup</h2>
        <p>Your data is stored locally. Backup is optional but recommended.</p>
      </div>

      {/* Storage Status */}
      <div className="status-section">
        <h3>💾 Local Storage Status</h3>
        <div className="status-grid">
          <div className="status-card">
            <div className="status-icon">👥</div>
            <div className="status-info">
              <div className="status-number">{storageStatus.local_storage.clients}</div>
              <div className="status-label">Clients</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">💰</div>
            <div className="status-info">
              <div className="status-number">{storageStatus.local_storage.payments}</div>
              <div className="status-label">Payments</div>
            </div>
          </div>
          
          <div className="status-card">
            <div className="status-icon">📦</div>
            <div className="status-info">
              <div className="status-number">{storageStatus.backup_status.items_needing_backup}</div>
              <div className="status-label">Need Backup</div>
            </div>
          </div>
        </div>

        <div className="last-backup">
          <strong>Last Backup:</strong> {
            storageStatus.backup_status.last_backup 
              ? new Date(storageStatus.backup_status.last_backup).toLocaleString()
              : 'Never'
          }
        </div>
      </div>

      {/* Manual Backup Controls */}
      <div className="backup-section">
        <h3>💾 Manual Backup</h3>
        <div className="backup-controls">
          <button 
            className="btn btn-primary"
            onClick={handleManualBackup}
            disabled={isBackingUp}
          >
            {isBackingUp ? '⏳ Creating Backup...' : '📥 Download Backup File'}
          </button>
          
          <div className="file-input-wrapper">
            <input
              type="file"
              accept=".json"
              onChange={handleRestoreFile}
              id="restore-file"
              style={{ display: 'none' }}
            />
            <button 
              className="btn btn-secondary"
              onClick={() => document.getElementById('restore-file').click()}
            >
              📤 Restore from File
            </button>
          </div>
        </div>
        <p className="help-text">
          Download your data as a JSON file. Keep it safe - it contains all your gym data!
        </p>
      </div>

      {/* Cloud Backup Settings */}
      <div className="cloud-section">
        <h3>☁️ Cloud Backup (Optional)</h3>
        
        <div className="cloud-provider-selection">
          <label>Cloud Provider:</label>
          <select 
            value={syncSettings.cloudProvider}
            onChange={(e) => updateSyncSettings({ cloudProvider: e.target.value })}
          >
            <option value="none">None (Local Only)</option>
            <option value="dropbox">Dropbox</option>
            <option value="googledrive">Google Drive</option>
            <option value="custom">Custom API</option>
          </select>
        </div>

        {syncSettings.cloudProvider !== 'none' && (
          <>
            <div className="auto-backup-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={syncSettings.autoBackup}
                  onChange={(e) => updateSyncSettings({ autoBackup: e.target.checked })}
                />
                Enable automatic cloud backup
              </label>
            </div>

            {syncSettings.autoBackup && (
              <div className="backup-frequency">
                <label>Backup Frequency:</label>
                <select 
                  value={syncSettings.backupFrequency}
                  onChange={(e) => updateSyncSettings({ backupFrequency: e.target.value })}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            )}

            <button 
              className="btn btn-cloud"
              onClick={handleCloudSync}
              disabled={isBackingUp}
            >
              {isBackingUp ? '⏳ Syncing...' : '☁️ Sync to Cloud Now'}
            </button>
          </>
        )}

        <div className="cloud-info">
          <h4>🔒 Privacy Notice:</h4>
          <ul>
            <li>✅ Your data stays on your device by default</li>
            <li>☁️ Cloud backup is entirely optional</li>
            <li>🔐 You control what gets backed up and when</li>
            <li>❌ No automatic data collection or sharing</li>
          </ul>
        </div>
      </div>

      {/* Backup History */}
      {backupHistory.length > 0 && (
        <div className="history-section">
          <h3>📋 Recent Backups</h3>
          <div className="backup-history">
            {backupHistory.slice(-5).map((backup, index) => (
              <div key={index} className={`backup-entry ${backup.status}`}>
                <div className="backup-time">
                  {new Date(backup.timestamp).toLocaleString()}
                </div>
                <div className="backup-type">
                  {backup.type === 'manual' ? '💾' : '☁️'} {backup.type}
                  {backup.provider && ` (${backup.provider})`}
                </div>
                <div className={`backup-status ${backup.status}`}>
                  {backup.status === 'success' ? '✅' : '❌'} {backup.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Export Options */}
      <div className="export-section">
        <h3>📊 Data Export</h3>
        <div className="export-options">
          <button className="btn btn-outline">
            📑 Export to CSV
          </button>
          <button className="btn btn-outline">
            📈 Export to Excel
          </button>
          <button className="btn btn-outline">
            📄 Export to PDF Report
          </button>
        </div>
      </div>

      <style jsx>{`
        .backup-control-panel {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }

        .panel-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .panel-header h2 {
          color: #2d3748;
          margin-bottom: 10px;
        }

        .panel-header p {
          color: #718096;
          font-size: 16px;
        }

        .status-section, .backup-section, .cloud-section, 
        .history-section, .export-section {
          background: white;
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .status-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          margin: 15px 0;
        }

        .status-card {
          display: flex;
          align-items: center;
          padding: 15px;
          background: #f8fafc;
          border-radius: 8px;
          border-left: 4px solid #56ab2f;
        }

        .status-icon {
          font-size: 24px;
          margin-right: 12px;
        }

        .status-number {
          font-size: 24px;
          font-weight: bold;
          color: #2d3748;
        }

        .status-label {
          font-size: 14px;
          color: #718096;
        }

        .backup-controls {
          display: flex;
          gap: 15px;
          margin: 15px 0;
          flex-wrap: wrap;
        }

        .btn {
          padding: 12px 20px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-primary {
          background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
          color: white;
        }

        .btn-secondary {
          background: #e2e8f0;
          color: #4a5568;
        }

        .btn-cloud {
          background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
          color: white;
        }

        .btn-outline {
          background: transparent;
          border: 2px solid #e2e8f0;
          color: #4a5568;
        }

        .btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .cloud-provider-selection, .backup-frequency {
          margin: 15px 0;
        }

        .cloud-provider-selection label, .backup-frequency label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
          color: #4a5568;
        }

        .cloud-provider-selection select, .backup-frequency select {
          padding: 8px 12px;
          border: 2px solid #e2e8f0;
          border-radius: 6px;
          font-size: 14px;
          background: white;
        }

        .auto-backup-toggle {
          margin: 15px 0;
        }

        .auto-backup-toggle label {
          display: flex;
          align-items: center;
          cursor: pointer;
          color: #4a5568;
        }

        .auto-backup-toggle input {
          margin-right: 8px;
        }

        .cloud-info {
          margin-top: 20px;
          padding: 15px;
          background: #f0fff4;
          border-radius: 8px;
          border-left: 4px solid #56ab2f;
        }

        .cloud-info h4 {
          margin: 0 0 10px 0;
          color: #2d3748;
        }

        .cloud-info ul {
          margin: 0;
          padding-left: 20px;
        }

        .cloud-info li {
          margin-bottom: 5px;
          color: #4a5568;
        }

        .backup-history {
          space: 10px 0;
        }

        .backup-entry {
          display: grid;
          grid-template-columns: 1fr auto auto;
          gap: 15px;
          padding: 10px 15px;
          border-radius: 6px;
          margin-bottom: 8px;
          align-items: center;
        }

        .backup-entry.success {
          background: #f0fff4;
          border-left: 4px solid #56ab2f;
        }

        .backup-entry.failed {
          background: #fef5e7;
          border-left: 4px solid #ed8936;
        }

        .backup-time {
          font-size: 14px;
          color: #4a5568;
        }

        .backup-type {
          font-size: 14px;
          font-weight: 500;
          color: #2d3748;
        }

        .backup-status.success {
          color: #56ab2f;
          font-weight: 500;
        }

        .backup-status.failed {
          color: #ed8936;
          font-weight: 500;
        }

        .export-options {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .help-text {
          font-size: 14px;
          color: #718096;
          margin-top: 10px;
          line-height: 1.5;
        }

        .last-backup {
          margin-top: 15px;
          padding: 10px;
          background: #f8fafc;
          border-radius: 6px;
          color: #4a5568;
        }

        @media (max-width: 600px) {
          .backup-controls {
            flex-direction: column;
          }
          
          .btn {
            width: 100%;
          }
          
          .backup-entry {
            grid-template-columns: 1fr;
            gap: 5px;
          }
          
          .status-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default BackupControlPanel;