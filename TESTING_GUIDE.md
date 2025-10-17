# Coffee Calculator - Testing Guide

## 🚀 Quick Start

### Local Testing (Windows)

1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```powershell
   python app.py
   ```

3. **Open in browser:**
   ```
   http://localhost:5000
   ```

4. **You'll be redirected to the login page** - Register a new account first!

## 📋 Complete Test Checklist

### 1. User Registration & Authentication ✅

- [ ] Navigate to `http://localhost:5000/register`
- [ ] Fill in:
  - Name: "Test User"
  - Email: "test@example.com"
  - Password: "password123"
  - Confirm Password: "password123"
- [ ] Click "Create Account"
- [ ] Should redirect to main calculator page
- [ ] Check that user name appears in top-right corner

### 2. Tea Bag Management 🍵

- [ ] Scroll to "Tea Bags & Per-Unit Items" section
- [ ] Click "➕ Add Tea Bag"
- [ ] Enter:
  - Name: "Earl Grey"
  - Cost: 0.25
- [ ] Click outside the input (auto-saves)
- [ ] Add another:
  - Name: "Green Tea"
  - Cost: 0.30
- [ ] Verify both tea bags appear in the list
- [ ] Try deleting one (click 🗑️ button)

### 3. Create a Drink with Custom Items ☕

- [ ] Enter ingredient costs:
  - Coffee Beans: 15.00 (€/kg)
  - Milk: 1.50 (€/L)
- [ ] In the drink card, enter name: "Cappuccino"
- [ ] Add ingredient:
  - Select "Coffee Beans"
  - Amount: 18 (grams)
- [ ] Click "+ Add Ingredient"
- [ ] Add another:
  - Select "Milk"
  - Amount: 100 (ml)
- [ ] Scroll down to "🍪 Custom Items"
- [ ] Click "➕ Add Custom Item"
- [ ] Enter:
  - Item name: "Cookie"
  - Cost: 0.50
- [ ] Add another custom item:
  - Item name: "Napkin"
  - Cost: 0.05

### 4. Calculate Costs 💰

- [ ] Add cleaning cost: 10.00 (€)
- [ ] Products per day: 50
- [ ] Click "💰 Calculate Costs"
- [ ] Verify results show:
  - Coffee Beans: 18.0 g at €15.00/kg = €0.27
  - Milk: 100.0 ml at €1.50/L = €0.15
  - Cookie: 1 item at €0.50 = €0.50
  - Napkin: 1 item at €0.05 = €0.05
  - Cleaning Cost: €0.20 (10/50)
  - **Total: €1.17**

### 5. Save Configuration 💾

- [ ] Click "💾 Save Current" in sidebar
- [ ] Enter name: "Test Menu"
- [ ] Click "Save"
- [ ] Verify it appears in the sidebar
- [ ] Check that it's marked as active (highlighted)

### 6. Configuration Sharing 🤝

#### Setup Second User:
- [ ] Open an incognito/private window
- [ ] Go to `http://localhost:5000/register`
- [ ] Register second user:
  - Name: "Second User"
  - Email: "second@example.com"
  - Password: "password123"

#### Share Configuration:
- [ ] In your original window (first user), click the 📤 share button next to "Test Menu"
- [ ] Enter email: "second@example.com"
- [ ] Check "Allow editing"
- [ ] Click "Share"
- [ ] Should see "Configuration shared successfully!"
- [ ] Verify "Second User" appears in the shared users list

#### Test Shared Access:
- [ ] In the incognito window (second user), refresh the page
- [ ] Check sidebar - should see "🔗 Test Menu by Test User"
- [ ] Click to load it
- [ ] Verify all ingredients, tea bags, and custom items load correctly
- [ ] Try making a change and saving (should work since "allow editing" was checked)

### 7. Tea Bags in Calculations 🍵

- [ ] Create a new drink: "Earl Grey Tea"
- [ ] DON'T add regular ingredients
- [ ] In "Custom Items" section, add:
  - Name: "Earl Grey" (matching tea bag name)
  - Cost: 0.25
- [ ] Note: Tea bags integration would need UI update to select from tea bag dropdown instead of custom items
- [ ] Calculate costs
- [ ] Verify tea bag cost appears correctly

### 8. Download PDF 📄

- [ ] After calculating costs, click "📄 Download PDF Report"
- [ ] Verify PDF downloads with:
  - All drinks listed
  - Ingredient breakdown
  - Custom items shown
  - Cleaning costs
  - Correct totals

### 9. Logout & Login 🚪

- [ ] Click "Logout" button (top-right)
- [ ] Should redirect to login page
- [ ] Try logging in with:
  - Email: "test@example.com"
  - Password: "password123"
- [ ] Should redirect back to calculator
- [ ] Verify your saved configurations are still there

### 10. Remove Sharing Access 🔒

- [ ] Load your shared configuration
- [ ] Click 📤 share button
- [ ] Click "Remove" next to "Second User"
- [ ] Confirm removal
- [ ] In incognito window (second user), refresh
- [ ] Shared configuration should disappear from sidebar

## 🐛 Common Issues & Solutions

### Issue: "401 Unauthorized" errors
**Solution:** Make sure you're logged in. Clear cookies and log in again.

### Issue: Tea bags not saving
**Solution:** Make sure to enter both name AND cost before clicking outside the input.

### Issue: Configuration won't load
**Solution:** Check browser console (F12) for errors. Make sure database is initialized.

### Issue: Can't see logout button
**Solution:** Make sure you're on the main page (not login/register). Check browser width (responsive design).

### Issue: Custom items not showing in breakdown
**Solution:** Make sure to enter both name and cost. Click "Calculate Costs" again.

## 📊 Expected Database Tables

After running the app, check the database has these tables:

```sql
-- View tables
sqlite3 data/coffee_calculator.db ".tables"
```

Should show:
- users
- configurations
- shared_configs
- tea_bags

## 🎯 Advanced Testing

### Test Permissions:

1. **View-Only Sharing:**
   - Share config without "Allow editing"
   - Second user should see but not delete/modify

2. **Multiple Collaborators:**
   - Register a third user
   - Share same config with multiple users
   - Verify all can access

3. **Concurrent Edits:**
   - First user edits config
   - Second user (with edit access) makes different edits
   - Last save should win

### Test Edge Cases:

- [ ] Create drink with no ingredients (should not save)
- [ ] Enter negative costs (should handle gracefully)
- [ ] Try to share with non-existent email
- [ ] Try to share with yourself
- [ ] Delete a configuration that's shared
- [ ] Load configuration with missing ingredients

## ✅ Success Criteria

All features working if:
- ✅ Can register and login
- ✅ Can create and save configurations
- ✅ Can add tea bags with per-unit costs
- ✅ Can add custom items to drinks
- ✅ Calculations include all item types
- ✅ Can share configurations with specific users
- ✅ Shared users can view/edit based on permissions
- ✅ Can remove sharing access
- ✅ PDF export includes all cost items
- ✅ Logout works and redirects properly

## 🚀 Production Deployment

Once local testing is complete:

```bash
# On your server
git pull
sudo ./install.sh
# Select option 2 (Update)

# Navigate to your domain
# Register first user
# Start using!
```

## 🔐 Security Notes

- Passwords are hashed with bcrypt
- SECRET_KEY is auto-generated by install.sh
- Sessions are secure and HTTP-only
- All API endpoints require authentication
- Per-user data isolation is enforced

---

**Happy Testing! ☕🎉**

If you encounter any issues, check:
1. Browser console (F12 → Console tab)
2. Terminal where app.py is running
3. Database file exists: `data/coffee_calculator.db`
