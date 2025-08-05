/**
 * Conflict Resolution System for Local-First Architecture
 * Handles conflicts when local and remote data differ
 */

class ConflictResolver {
  constructor(localFirstManager) {
    this.localManager = localFirstManager;
    this.conflictStrategies = {
      'last_write_wins': this.lastWriteWins.bind(this),
      'user_choice': this.userChoice.bind(this),
      'merge_fields': this.mergeFields.bind(this),
      'keep_both': this.keepBoth.bind(this)
    };
  }

  async detectConflicts(localData, remoteData) {
    const conflicts = [];
    
    // Group data by type and ID for comparison
    const localByType = this.groupDataByType(localData);
    const remoteByType = this.groupDataByType(remoteData);
    
    // Check each data type for conflicts
    for (const dataType of ['clients', 'payments']) {
      const localItems = localByType[dataType] || {};
      const remoteItems = remoteByType[dataType] || {};
      
      // Find items that exist in both with different timestamps
      for (const itemId in localItems) {
        if (remoteItems[itemId]) {
          const localItem = localItems[itemId];
          const remoteItem = remoteItems[itemId];
          
          // Check if they differ (excluding timestamps)
          if (this.itemsConflict(localItem, remoteItem)) {
            conflicts.push({
              type: dataType,
              id: itemId,
              local: localItem,
              remote: remoteItem,
              conflictFields: this.identifyConflictingFields(localItem, remoteItem)
            });
          }
        }
      }
    }
    
    return conflicts;
  }

  groupDataByType(data) {
    const grouped = { clients: {}, payments: {} };
    
    if (data.clients) {
      data.clients.forEach(item => {
        grouped.clients[item.id] = item;
      });
    }
    
    if (data.payments) {
      data.payments.forEach(item => {
        grouped.payments[item.id] = item;
      });
    }
    
    return grouped;
  }

  itemsConflict(localItem, remoteItem) {
    // Compare items excluding metadata fields
    const excludeFields = ['updated_at', 'created_at', '_local_only', 'last_synced'];
    
    for (const field in localItem) {
      if (excludeFields.includes(field)) continue;
      
      if (localItem[field] !== remoteItem[field]) {
        return true;
      }
    }
    
    for (const field in remoteItem) {
      if (excludeFields.includes(field)) continue;
      
      if (localItem[field] !== remoteItem[field]) {
        return true;
      }
    }
    
    return false;
  }

  identifyConflictingFields(localItem, remoteItem) {
    const conflicts = [];
    const excludeFields = ['updated_at', 'created_at', '_local_only', 'last_synced'];
    
    const allFields = new Set([...Object.keys(localItem), ...Object.keys(remoteItem)]);
    
    for (const field of allFields) {
      if (excludeFields.includes(field)) continue;
      
      if (localItem[field] !== remoteItem[field]) {
        conflicts.push({
          field,
          local: localItem[field],
          remote: remoteItem[field]
        });
      }
    }
    
    return conflicts;
  }

  // Strategy 1: Last Write Wins
  async lastWriteWins(conflict) {
    const localTime = new Date(conflict.local.updated_at).getTime();
    const remoteTime = new Date(conflict.remote.updated_at).getTime();
    
    const winner = localTime > remoteTime ? conflict.local : conflict.remote;
    const source = localTime > remoteTime ? 'local' : 'remote';
    
    console.log(`🏆 Last Write Wins: Using ${source} version for ${conflict.type} ${conflict.id}`);
    
    return {
      resolution: 'last_write_wins',
      chosen: winner,
      source: source
    };
  }

  // Strategy 2: User Choice
  async userChoice(conflict) {
    return new Promise((resolve) => {
      this.showConflictModal(conflict, (choice) => {
        const chosen = choice === 'local' ? conflict.local : conflict.remote;
        resolve({
          resolution: 'user_choice',
          chosen: chosen,
          source: choice
        });
      });
    });
  }

  // Strategy 3: Merge Fields
  async mergeFields(conflict) {
    const merged = { ...conflict.remote }; // Start with remote as base
    
    // Apply field-level merging rules
    for (const fieldConflict of conflict.conflictFields) {
      const field = fieldConflict.field;
      
      switch (field) {
        case 'name':
        case 'email':
          // For critical fields, prefer local changes
          merged[field] = conflict.local[field];
          break;
          
        case 'monthly_fee':
          // For financial fields, prefer higher value (assume updates)
          merged[field] = Math.max(
            conflict.local[field] || 0, 
            conflict.remote[field] || 0
          );
          break;
          
        case 'amount_owed':
          // For amounts owed, prefer lower value (payments reduce debt)
          merged[field] = Math.min(
            conflict.local[field] || 0, 
            conflict.remote[field] || 0
          );
          break;
          
        case 'payment_status':
          // Prefer 'paid' status over others
          merged[field] = (conflict.local[field] === 'paid' || conflict.remote[field] === 'paid') 
            ? 'paid' : conflict.local[field];
          break;
          
        default:
          // For other fields, prefer local changes
          merged[field] = conflict.local[field];
      }
    }
    
    // Update metadata
    merged.updated_at = new Date().toISOString();
    merged._merged = true;
    merged._merge_timestamp = new Date().toISOString();
    
    console.log(`🔗 Field Merge: Merged ${conflict.conflictFields.length} fields for ${conflict.type} ${conflict.id}`);
    
    return {
      resolution: 'merge_fields',
      chosen: merged,
      source: 'merged'
    };
  }

  // Strategy 4: Keep Both
  async keepBoth(conflict) {
    const localCopy = {
      ...conflict.local,
      id: `${conflict.local.id}_local_${Date.now()}`,
      name: `${conflict.local.name} (Local Copy)`,
      _conflict_copy: true
    };
    
    const remoteCopy = {
      ...conflict.remote,
      id: `${conflict.remote.id}_remote_${Date.now()}`,
      name: `${conflict.remote.name} (Remote Copy)`,
      _conflict_copy: true
    };
    
    console.log(`📋 Keep Both: Created copies for ${conflict.type} ${conflict.id}`);
    
    return {
      resolution: 'keep_both',
      chosen: [localCopy, remoteCopy],
      source: 'both'
    };
  }

  showConflictModal(conflict, callback) {
    // Create conflict resolution UI
    const modal = document.createElement('div');
    modal.className = 'conflict-modal-overlay';
    
    modal.innerHTML = `
      <div class="conflict-modal">
        <div class="conflict-header">
          <h3>🔄 Data Conflict Detected</h3>
          <p>The ${conflict.type} "${conflict.local.name || conflict.local.id}" has been modified both locally and remotely.</p>
        </div>
        
        <div class="conflict-comparison">
          <div class="conflict-option local">
            <h4>📱 Local Version</h4>
            <div class="conflict-details">
              <div class="updated-time">Updated: ${new Date(conflict.local.updated_at).toLocaleString()}</div>
              ${this.renderConflictFields(conflict.conflictFields, 'local')}
            </div>
            <button class="btn btn-local" onclick="resolveConflict('local')">
              Use Local Version
            </button>
          </div>
          
          <div class="conflict-option remote">
            <h4>☁️ Remote Version</h4>
            <div class="conflict-details">
              <div class="updated-time">Updated: ${new Date(conflict.remote.updated_at).toLocaleString()}</div>
              ${this.renderConflictFields(conflict.conflictFields, 'remote')}
            </div>
            <button class="btn btn-remote" onclick="resolveConflict('remote')">
              Use Remote Version
            </button>
          </div>
        </div>
        
        <div class="conflict-actions">
          <button class="btn btn-merge" onclick="resolveConflict('merge')">
            🔗 Smart Merge
          </button>
          <button class="btn btn-both" onclick="resolveConflict('both')">
            📋 Keep Both
          </button>
        </div>
      </div>
    `;
    
    // Add to DOM
    document.body.appendChild(modal);
    
    // Add global resolver function
    window.resolveConflict = (choice) => {
      document.body.removeChild(modal);
      delete window.resolveConflict;
      callback(choice);
    };
    
    // Add styles
    this.addConflictModalStyles();
  }

  renderConflictFields(conflictFields, source) {
    return conflictFields.map(field => `
      <div class="conflict-field">
        <strong>${field.field}:</strong> 
        <span class="field-value">${field[source] || 'undefined'}</span>
      </div>
    `).join('');
  }

  addConflictModalStyles() {
    if (document.getElementById('conflict-modal-styles')) return;
    
    const styles = document.createElement('style');
    styles.id = 'conflict-modal-styles';
    styles.textContent = `
      .conflict-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
      }
      
      .conflict-modal {
        background: white;
        border-radius: 12px;
        padding: 24px;
        max-width: 800px;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      }
      
      .conflict-header {
        text-align: center;
        margin-bottom: 24px;
      }
      
      .conflict-header h3 {
        color: #e53e3e;
        margin-bottom: 8px;
      }
      
      .conflict-comparison {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 24px;
      }
      
      .conflict-option {
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
      }
      
      .conflict-option.local {
        border-color: #3182ce;
      }
      
      .conflict-option.remote {
        border-color: #38a169;
      }
      
      .conflict-option h4 {
        margin: 0 0 12px 0;
        color: #2d3748;
      }
      
      .updated-time {
        font-size: 12px;
        color: #718096;
        margin-bottom: 12px;
      }
      
      .conflict-field {
        margin-bottom: 8px;
        padding: 6px 0;
        border-bottom: 1px solid #f7fafc;
      }
      
      .field-value {
        color: #4a5568;
        font-family: monospace;
        background: #f7fafc;
        padding: 2px 6px;
        border-radius: 4px;
      }
      
      .conflict-actions {
        display: flex;
        gap: 12px;
        justify-content: center;
        flex-wrap: wrap;
      }
      
      .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }
      
      .btn-local {
        background: #3182ce;
        color: white;
      }
      
      .btn-remote {
        background: #38a169;
        color: white;
      }
      
      .btn-merge {
        background: #805ad5;
        color: white;
      }
      
      .btn-both {
        background: #ed8936;
        color: white;
      }
      
      .btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
      
      @media (max-width: 600px) {
        .conflict-comparison {
          grid-template-columns: 1fr;
        }
        
        .conflict-actions {
          flex-direction: column;
        }
      }
    `;
    
    document.head.appendChild(styles);
  }

  async resolveConflicts(conflicts, strategy = 'user_choice') {
    const resolutions = [];
    
    for (const conflict of conflicts) {
      console.log(`🔄 Resolving conflict for ${conflict.type} ${conflict.id} using ${strategy} strategy`);
      
      const resolution = await this.conflictStrategies[strategy](conflict);
      resolutions.push({
        conflict,
        resolution
      });
    }
    
    return resolutions;
  }

  async applyResolutions(resolutions) {
    for (const { conflict, resolution } of resolutions) {
      try {
        if (resolution.resolution === 'keep_both') {
          // Add both items
          for (const item of resolution.chosen) {
            await this.localManager.addOrUpdateItem(conflict.type, item);
          }
        } else {
          // Update with chosen item
          await this.localManager.addOrUpdateItem(conflict.type, resolution.chosen);
        }
        
        console.log(`✅ Applied resolution for ${conflict.type} ${conflict.id}`);
      } catch (error) {
        console.error(`❌ Failed to apply resolution for ${conflict.type} ${conflict.id}:`, error);
      }
    }
  }
}

export default ConflictResolver;