# Coffee Calculator - Multi-User Authentication & Tea Bags Upgrade Guide

## Overview
This upgrade adds:
- 🔐 **User Authentication** (Login/Register/Logout)
- 👥 **Per-User Configurations** with sharing capabilities
- 🍵 **Tea Bag Management** (per-unit cost items)
- 🍪 **Custom Items** per drink (cookies, etc.)
- 🤝 **Configuration Collaboration** (share with edit/view permissions)

## Files Modified/Created

### ✅ Completed Backend Changes

1. **requirements.txt** - Added Flask-Login and Flask-Bcrypt
2. **app.py** - Complete authentication system with new endpoints:
   - `/login` - Login page
   - `/register` - Registration page
   - `/api/register` - User registration API
   - `/api/login` - User login API
   - `/api/logout` - Logout API
   - `/api/tea-bags` - Tea bag CRUD operations
   - `/api/configs/<id>/share` - Share configuration
   - `/api/configs/<id>/shared-users` - Get shared users list
   - `/api/configs/<id>/unshare/<user_id>` - Remove sharing

3. **templates/login.html** ✅ Created
4. **templates/register.html** ✅ Created

### 🔄 Frontend Changes Needed

#### templates/index.html

**User Menu Added:** The logout button and user display have been added to the header.

**Still Need to Add:**

1. **Tea Bag Management Section** (add after ingredient costs section):

```html
<!-- Add this new section after the Ingredient Costs section -->
<div class="section">
    <h2>🍵 Tea Bags & Per-Unit Items</h2>
    <p style="margin-bottom: 15px; color: #666;">
        Enter the cost per tea bag or per-unit item
    </p>
    
    <div class="ingredient-grid">
        <div id="tea-bag-inputs">
            <!-- Dynamically populated tea bags -->
        </div>
        <button class="btn" onclick="addTeaBag()" style="margin-top: 10px;">
            ➕ Add Tea Bag
        </button>
    </div>
</div>
```

2. **Custom Items in Drink Cards** (modify addDrink() HTML):

Add this section inside each drink card (after the ingredients section):

```html
<div class="custom-items-section" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
    <h4 style="margin-bottom: 10px; color: #667eea;">Custom Items (Cookies, etc.)</h4>
    <div id="custom-items-${drinkCounter}">
        <!-- Custom items will be added here -->
    </div>
    <button class="btn" onclick="addCustomItem(${drinkCounter})" style="margin-top: 10px; font-size: 0.9em;">
        ➕ Add Custom Item
    </button>
</div>
```

3. **Share Button in Sidebar** (add to config item template):

```html
<button class="share-btn" onclick="showShareModal(configId)" title="Share">📤</button>
```

4. **Share Modal** (add before closing body tag):

```html
<div id="shareModal" class="modal">
    <div class="modal-content">
        <h2>🤝 Share Configuration</h2>
        <p>Share "<span id="share-config-name"></span>" with another user</p>
        
        <div class="form-group" style="margin: 20px 0;">
            <label>User Email:</label>
            <input type="email" id="shareEmail" placeholder="user@example.com" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #ddd;">
        </div>
        
        <div class="form-group" style="margin: 20px 0;">
            <label>
                <input type="checkbox" id="shareCanEdit" style="margin-right: 8px;">
                Allow editing
            </label>
        </div>
        
        <div id="sharedUsersList" style="margin: 20px 0; max-height: 200px; overflow-y: auto;">
            <!-- List of users already shared with -->
        </div>
        
        <div class="modal-actions">
            <button class="modal-btn modal-btn-secondary" onclick="closeShareModal()">Cancel</button>
            <button class="modal-btn modal-btn-primary" onclick="shareConfiguration()">Share</button>
        </div>
    </div>
</div>
```

#### static/app.js

**Need to Add These Functions:**

```javascript
// Logout function
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Tea bag management
let teaBags = {}; // Store tea bag data

async function loadTeaBags() {
    try {
        const response = await fetch('/api/tea-bags', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            teaBags = {};
            const container = document.getElementById('tea-bag-inputs');
            container.innerHTML = '';
            
            data.tea_bags.forEach(bag => {
                teaBags[bag.name] = bag.cost_per_unit;
                addTeaBagInput(bag.name, bag.cost_per_unit, bag.id);
            });
        }
    } catch (error) {
        console.error('Error loading tea bags:', error);
    }
}

function addTeaBagInput(name = '', cost = '', id = null) {
    const container = document.getElementById('tea-bag-inputs');
    const teaBagId = id || `teabag-${Date.now()}`;
    
    const html = `
        <div class="ingredient-input" data-teabag-id="${teaBagId}">
            <div style="display: flex; gap: 10px; align-items: center;">
                <input type="text" 
                       placeholder="Tea Bag Name" 
                       value="${name}"
                       onchange="saveTeaBag(this)"
                       style="flex: 2;">
                <input type="number" 
                       placeholder="0.00" 
                       value="${cost}"
                       step="0.01"
                       onchange="saveTeaBag(this)"
                       style="flex: 1;">
                <button onclick="deleteTeaBag(${teaBagId})" 
                        style="background: #e74c3c; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">
                    🗑️
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
}

async function saveTeaBag(input) {
    const container = input.closest('[data-teabag-id]');
    const inputs = container.querySelectorAll('input');
    const name = inputs[0].value.trim();
    const cost = parseFloat(inputs[1].value) || 0;
    const id = container.dataset.teabagId !== 'new' ? container.dataset.teabagId : null;
    
    if (!name || cost <= 0) return;
    
    try {
        const response = await fetch('/api/tea-bags', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ id, name, cost_per_unit: cost })
        });
        
        const data = await response.json();
        if (data.success) {
            teaBags[name] = cost;
            console.log('Tea bag saved');
        }
    } catch (error) {
        console.error('Error saving tea bag:', error);
    }
}

async function deleteTeaBag(id) {
    if (!confirm('Delete this tea bag?')) return;
    
    try {
        const response = await fetch(`/api/tea-bags/${id}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadTeaBags();
        }
    } catch (error) {
        console.error('Error deleting tea bag:', error);
    }
}

function addTeaBag() {
    addTeaBagInput();
}

// Custom items management
function addCustomItem(drinkId) {
    const container = document.getElementById(`custom-items-${drinkId}`);
    const itemId = `custom-${drinkId}-${Date.now()}`;
    
    const html = `
        <div class="custom-item-row" data-item-id="${itemId}" style="display: flex; gap: 10px; margin-bottom: 10px;">
            <input type="text" 
                   placeholder="Item name (e.g., Cookie)" 
                   class="custom-item-name"
                   style="flex: 2; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
            <input type="number" 
                   placeholder="Cost (€)" 
                   class="custom-item-cost"
                   step="0.01"
                   style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #ddd;">
            <button onclick="this.parentElement.remove()" 
                    style="background: #e74c3c; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">
                ✕
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
}

// Sharing functionality
let currentShareConfigId = null;

function showShareModal(configId) {
    currentShareConfigId = configId;
    const modal = document.getElementById('shareModal');
    const configName = document.querySelector(`[data-config-id="${configId}"] .config-name`).textContent;
    document.getElementById('share-config-name').textContent = configName;
    
    loadSharedUsers(configId);
    modal.style.display = 'flex';
}

function closeShareModal() {
    document.getElementById('shareModal').style.display = 'none';
    document.getElementById('shareEmail').value = '';
    document.getElementById('shareCanEdit').checked = false;
}

async function loadSharedUsers(configId) {
    try {
        const response = await fetch(`/api/configs/${configId}/shared-users`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('sharedUsersList');
            if (data.shared_users.length === 0) {
                container.innerHTML = '<p style="color: #999; text-align: center;">Not shared yet</p>';
            } else {
                container.innerHTML = '<h4 style="margin-bottom: 10px;">Shared with:</h4>';
                data.shared_users.forEach(user => {
                    container.innerHTML += `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 6px; margin-bottom: 5px;">
                            <span>${user.name} (${user.email}) - ${user.can_edit ? '✏️ Can Edit' : '👁️ View Only'}</span>
                            <button onclick="unshareWith(${configId}, ${user.user_id})" 
                                    style="background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 4px; cursor: pointer; font-size: 0.85em;">
                                Remove
                            </button>
                        </div>
                    `;
                });
            }
        }
    } catch (error) {
        console.error('Error loading shared users:', error);
    }
}

async function shareConfiguration() {
    const email = document.getElementById('shareEmail').value.trim();
    const canEdit = document.getElementById('shareCanEdit').checked;
    
    if (!email) {
        alert('Please enter an email address');
        return;
    }
    
    try {
        const response = await fetch(`/api/configs/${currentShareConfigId}/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, can_edit: canEdit })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Configuration shared successfully!');
            document.getElementById('shareEmail').value = '';
            loadSharedUsers(currentShareConfigId);
        } else {
            alert(data.error || 'Failed to share configuration');
        }
    } catch (error) {
        console.error('Error sharing configuration:', error);
        alert('Network error. Please try again.');
    }
}

async function unshareWith(configId, userId) {
    if (!confirm('Remove sharing access for this user?')) return;
    
    try {
        const response = await fetch(`/api/configs/${configId}/unshare/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (response.ok) {
            loadSharedUsers(configId);
        }
    } catch (error) {
        console.error('Error removing share:', error);
    }
}

// Update collectData() to include tea bags and custom items
function collectData() {
    // ... existing code ...
    
    // Add tea bags to data
    data.tea_bags = teaBags;
    
    // Add custom items to each drink
    drinks.forEach((drink, index) => {
        const drinkId = index + 1;
        const customItemsContainer = document.getElementById(`custom-items-${drinkId}`);
        const customItems = [];
        
        if (customItemsContainer) {
            customItemsContainer.querySelectorAll('.custom-item-row').forEach(row => {
                const name = row.querySelector('.custom-item-name').value.trim();
                const cost = parseFloat(row.querySelector('.custom-item-cost').value) || 0;
                
                if (name && cost > 0) {
                    customItems.push({ name, cost });
                }
            });
        }
        
        drink.custom_items = customItems;
    });
    
    return data;
}

// Initialize tea bags on load
document.addEventListener('DOMContentLoaded', function() {
    addDrink();
    loadConfigurations();
    loadTeaBags(); // Add this line
});
```

## Database Schema

The new schema includes:

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configurations (now with user_id)
ALTER TABLE configurations ADD COLUMN user_id INTEGER;

-- Shared configurations
CREATE TABLE shared_configs (
    id INTEGER PRIMARY KEY,
    config_id INTEGER,
    shared_with_user_id INTEGER,
    can_edit BOOLEAN DEFAULT 0,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES configurations(id),
    FOREIGN KEY (shared_with_user_id) REFERENCES users(id)
);

-- Tea bags
CREATE TABLE tea_bags (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT NOT NULL,
    cost_per_unit REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Deployment Steps

1. **Backup existing database:**
   ```bash
   cp data/coffee_calculator.db data/coffee_calculator.db.backup
   ```

2. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create first user:**
   - Navigate to `/register`
   - Create your account

4. **Migrate existing configs:**
   - All existing configurations will be assigned to user_id = 1
   - First registered user will own them

5. **Update and restart:**
   ```bash
   sudo ./install.sh
   # Select option 2 (Update)
   ```

## Features Summary

### Authentication
- ✅ Secure password hashing with bcrypt
- ✅ Session-based authentication
- ✅ Login/Register/Logout functionality
- ✅ Protected routes (must be logged in)

### Configuration Sharing
- ✅ Share configs with other users by email
- ✅ Set view-only or edit permissions
- ✅ View shared configs in sidebar with owner name
- ✅ Remove sharing access

### Tea Bags
- ✅ Manage per-unit cost items
- ✅ Use in drink recipes
- ✅ Per-user tea bag library

### Custom Items
- ✅ Add one-off items to drinks (cookies, napkins, etc.)
- ✅ Fixed cost per item
- ✅ Flexible naming

## CSS Additions Needed

Add these styles to handle shared configurations and tea bags:

```css
.config-item.shared {
    border-left: 3px solid #3498db;
}

.config-owner {
    font-size: 0.8em;
    color: #7f8c8d;
    font-style: italic;
}

.share-btn {
    background: #3498db;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 4px;
    cursor: pointer;
    margin-left: 5px;
    font-size: 0.9em;
}

.share-btn:hover {
    background: #2980b9;
}

.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    justify-content: center;
    align-items: center;
    z-index: 1000;
}
```

## Testing Checklist

- [ ] Register new user
- [ ] Login with credentials
- [ ] Create configuration
- [ ] Add tea bag
- [ ] Use tea bag in drink
- [ ] Add custom item to drink
- [ ] Calculate costs
- [ ] Share configuration with another user
- [ ] Login as second user and view shared config
- [ ] Edit shared config (if permission granted)
- [ ] Logout

## Security Notes

- Passwords are hashed with bcrypt (never stored in plain text)
- Session-based authentication with secure cookies
- CORS configured for credential support
- All user-specific data is isolated by user_id
- Shared configurations require proper ownership checks

## Next Steps

1. Review this guide
2. Apply remaining frontend changes to `index.html` and `app.js`
3. Test authentication flow
4. Test sharing functionality
5. Deploy to server

---

**Need help?** All backend code is complete and ready. Frontend changes are documented above with copy-paste ready code snippets.
