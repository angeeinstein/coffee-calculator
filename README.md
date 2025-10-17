# ☕ Coffee Cost Calculator

A web application for calculating the cost of coffee drinks based on ingredient costs. Perfect for coffee shops, home baristas, or anyone who wants to track their coffee expenses.

## Features

- 📦 **Ingredient Management**: Define costs for multiple ingredients (coffee beans, milk, chocolate powder, etc.)
- 🍵 **Custom Drink Creation**: Create unlimited drinks with custom ingredient mixtures
- 💰 **Cost Calculation**: Automatic calculation of per-drink costs with detailed breakdowns
- � **Configuration Storage**: Save and load multiple configurations (e.g., different menus or recipes)
- 🗑️ **Config Management**: Easy management with save, load, and delete functionality
- �📄 **PDF Export**: Generate professional PDF reports with all cost information
- 🎨 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- 🚀 **Production Ready**: Runs as a systemd service with Gunicorn for high performance
- 🌐 **Server Ready**: Designed to run on Ubuntu server with Cloudflare tunnel support

## Quick Installation on Ubuntu Server

### One-Command Installation

1. **Clone the repository to your Ubuntu server**:
```bash
git clone https://github.com/angeeinstein/coffee-calculator.git
cd coffee-calculator
```

2. **Run the installation script**:
```bash
chmod +x install.sh
sudo ./install.sh
```

That's it! The script will:
- Install all system dependencies (Python, pip, build tools)
- Create a Python virtual environment
- Install all Python packages (Flask, Gunicorn, ReportLab, etc.)
- Set up the SQLite database for configuration storage
- Create and start a systemd service
- Configure automatic startup on boot

The application will be running at `http://localhost:5000` or `http://your-server-ip:5000`

### One-Command Update

To update to the latest version, simply run the install script again:

```bash
cd coffee-calculator
sudo ./install.sh
```

The script automatically:
- ✅ Detects that it's an update (not a fresh install)
- ✅ Creates a database backup
- ✅ Pulls the latest code from git
- ✅ Updates all dependencies
- ✅ Migrates the database schema
- ✅ Restarts the service
- ✅ Preserves all your saved configurations

**No manual git pull needed!** Just run `./install.sh` and everything is updated automatically.

## What the Installation Script Does

The `install.sh` script is fully automated and handles everything:

- ✅ Checks for and installs missing dependencies
- ✅ Creates isolated Python virtual environment
- ✅ Installs all required Python packages
- ✅ Sets up the data directory for SQLite database
- ✅ Configures proper file permissions
- ✅ Creates systemd service file
- ✅ Enables automatic startup on boot
- ✅ Starts the service immediately
- ✅ Provides detailed status and useful commands

## Manual Installation (if needed)

If you prefer to install manually or need to customize:

### Prerequisites

- Ubuntu Server (18.04 or later)
- Python 3.8 or higher
- pip (Python package manager)

### Installation on Ubuntu Server

### Prerequisites

- Ubuntu Server (18.04 or later)
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Upload the Project

```bash
# Create a directory for the application
mkdir -p ~/coffee-calculator
cd ~/coffee-calculator

# Upload all project files to this directory
```

### Step 2: Install Python Dependencies

```bash
# Update system packages
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Run the Application

```bash
# Make sure you're in the project directory with venv activated
source venv/bin/activate

# Run the Flask application
python app.py
```

The application will start on `http://0.0.0.0:5000`

### Step 4: Run as a Background Service (Optional but Recommended)

Create a systemd service file for automatic startup:

```bash
sudo nano /etc/systemd/system/coffee-calculator.service
```

Add the following content (replace `/home/yourusername` with your actual path):

```ini
[Unit]
Description=Coffee Cost Calculator
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/coffee-calculator
Environment="PATH=/home/yourusername/coffee-calculator/venv/bin"
ExecStart=/home/yourusername/coffee-calculator/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable coffee-calculator
sudo systemctl start coffee-calculator
sudo systemctl status coffee-calculator
```

## Setting Up Cloudflare Tunnel

Cloudflare Tunnel allows you to securely expose your application to the internet without opening firewall ports.

### Step 1: Install Cloudflared

```bash
# Download and install cloudflared
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

### Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

This will open a browser window (or provide a URL) to authenticate with your Cloudflare account.

### Step 3: Create a Tunnel

```bash
# Create a new tunnel
cloudflared tunnel create coffee-calculator

# Note the Tunnel ID from the output
```

### Step 4: Configure the Tunnel

Create a configuration file:

```bash
nano ~/.cloudflared/config.yml
```

Add the following content (replace `TUNNEL-ID` with your actual tunnel ID):

```yaml
tunnel: TUNNEL-ID
credentials-file: /home/yourusername/.cloudflared/TUNNEL-ID.json

ingress:
  - hostname: your-domain.com
    service: http://localhost:5000
  - service: http_status:404
```

### Step 5: Route DNS to Your Tunnel

```bash
cloudflared tunnel route dns coffee-calculator your-domain.com
```

### Step 6: Run the Tunnel

```bash
# Run the tunnel (test mode)
cloudflared tunnel run coffee-calculator

# Or install as a service for automatic startup
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

## Managing the Application

### Update or Uninstall

When you run the install script on an existing installation, you'll get an interactive menu:

```bash
cd coffee-calculator
sudo ./install.sh
```

You'll see:
```
Existing installation detected!

What would you like to do?

1) Update to latest version (pulls code, updates dependencies, restarts service)
2) Complete removal (uninstall service, remove all files and data)
3) Cancel
```

### Service Management

After installation, you can manage the application using systemd:

```bash
# Check service status
sudo systemctl status coffee-calculator

# Stop the service
sudo systemctl stop coffee-calculator

# Start the service
sudo systemctl start coffee-calculator

# Restart the service
sudo systemctl restart coffee-calculator

# View logs in real-time
sudo journalctl -u coffee-calculator -f

# Disable automatic startup
sudo systemctl disable coffee-calculator

# Enable automatic startup
sudo systemctl enable coffee-calculator
```

## Updating the Application

To update to the latest version, just run the install script again:

```bash
cd /path/to/coffee-calculator
sudo ./install.sh
```

That's it! The script automatically:
- Detects it's an update
- Backs up your database
- Pulls the latest code from git
- Updates dependencies
- Restarts the service

Your saved configurations are preserved during updates.

## Usage

### Basic Workflow

1. **Set Fixed Costs** (optional):
   - Daily Cleaning Cost: Enter in € (fixed cost per day)
   - Expected Products per Day: Number of products to distribute the cost

2. **Set Ingredient Costs**: Enter prices per kilogram (kg) or liter (L)
   - Solid ingredients: €/kg (Coffee Beans, Chocolate Powder, Sugar)
   - Liquid ingredients: €/L (Milk, Water, Vanilla Syrup)

3. **Define Drinks**: Click "Add New Drink" to create a drink
   - Name your drink (e.g., "Cappuccino")
   - Select ingredients from dropdown
   - Enter amounts in grams (g) or milliliters (ml)
   - Add multiple ingredients as needed

4. **Calculate**: Click "Calculate Costs" to see the breakdown
   - View ingredient costs
   - See cleaning cost per product (if set)
   - Get total cost per drink

5. **Download Report**: Click "Download PDF Report" to get a professional PDF

### Example

**Setting up ingredients:**
- Coffee Beans: €30.00/kg
- Milk: €1.20/L
- Daily Cleaning Cost: €50.00
- Expected Products per Day: 200

**Creating a Cappuccino:**
- Coffee Beans: 18 g
- Milk: 150 ml

**Result:**
- Coffee cost: €30/kg × 0.018 kg = €0.54
- Milk cost: €1.20/L × 0.15 L = €0.18
- Cleaning cost: €50/200 = €0.25
- **Total: €0.97 per Cappuccino**

### Configuration Management

1. **Save Configuration**: Click "💾 Save Current" in the sidebar
   - Enter a name (e.g., "Summer Menu", "Winter Specials")
   - Click Save
2. **Load Configuration**: Click on any saved configuration in the sidebar
3. **Delete Configuration**: Click the 🗑️ button next to a configuration
4. **New Configuration**: Click "📝 New Config" to start fresh

All configurations are automatically stored in the SQLite database on the server.

## Project Structure

```
coffee-calculator/
├── app.py                    # Flask backend server with API endpoints
├── requirements.txt          # Python dependencies (Flask, Gunicorn, ReportLab)
├── install.sh               # Automated installation script
├── README.md                # This file
├── .gitignore              # Git ignore patterns
├── data/                    # Created by install script
│   └── coffee_calculator.db # SQLite database for configurations
├── static/
│   └── app.js              # Frontend JavaScript with config management
└── templates/
    └── index.html          # HTML and CSS frontend with sidebar
```

## API Endpoints

- `GET /` - Main application page
- `POST /api/calculate` - Calculate drink costs
- `POST /api/generate-pdf` - Generate PDF report
- `GET /api/configs` - Get all saved configurations
- `GET /api/configs/<id>` - Get specific configuration
- `POST /api/configs` - Save new or update existing configuration
- `DELETE /api/configs/<id>` - Delete a configuration

## Troubleshooting

### Service won't start after installation
```bash
# Check service status and logs
sudo systemctl status coffee-calculator
sudo journalctl -u coffee-calculator -n 50

# Common fixes:
# 1. Ensure port 5000 is not in use
sudo lsof -i :5000

# 2. Check file permissions
ls -la /path/to/coffee-calculator

# 3. Verify Python environment
source /path/to/coffee-calculator/venv/bin/activate
python --version
pip list

# 4. Restart the service
sudo systemctl restart coffee-calculator
```

### Port 5000 already in use
If port 5000 is occupied, edit the systemd service file:
```bash
sudo nano /etc/systemd/system/coffee-calculator.service
```
Change the port in the ExecStart line:
```
ExecStart=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5001 ...
```
Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart coffee-calculator
```

### Database errors
```bash
# Check if database exists and has correct permissions
ls -la /path/to/coffee-calculator/data/

# If needed, recreate the database
rm /path/to/coffee-calculator/data/coffee_calculator.db
sudo systemctl restart coffee-calculator
```

### PDF generation fails
- Ensure reportlab is installed: `pip install reportlab`
- Check system dependencies: `sudo apt install python3-dev libfreetype6-dev`
- Restart the service after installing dependencies

### Cloudflare tunnel not working
- Verify cloudflared is running: `sudo systemctl status cloudflared`
- Check tunnel status: `cloudflared tunnel info coffee-calculator`
- Review logs: `journalctl -u cloudflared -f`
- Ensure tunnel points to correct port (5000 or your custom port)

### Configuration won't save
- Check database file permissions: `ls -la data/coffee_calculator.db`
- Verify data directory is writable: `ls -ld data/`
- Check service logs: `sudo journalctl -u coffee-calculator -f`

## Security Notes

- ✅ Application runs as systemd service with proper user isolation
- ✅ Gunicorn provides production-grade WSGI server
- ✅ Cloudflare Access handles authentication (as per your setup)
- ✅ SQLite database stored in protected data directory
- ⚠️ For production, consider:
  - Using a reverse proxy like Nginx for SSL/TLS
  - Setting up regular database backups
  - Monitoring logs for unusual activity
  - Keeping system and dependencies updated

## Uninstalling

To completely remove the application:

```bash
cd coffee-calculator
sudo ./install.sh
# Select option 2 (Complete removal)
```

The uninstall process will:
1. Stop and remove the systemd service
2. Remove the Python virtual environment
3. **Ask if you want to delete the database** (your configurations)
4. **Ask if you want to delete all application files**

This gives you full control over what gets removed.

## Database Backup

The update process automatically creates database backups. To manually backup:

```bash
# Backup database
sudo cp /path/to/coffee-calculator/data/coffee_calculator.db ~/coffee_calculator_backup_$(date +%Y%m%d).db

# Restore database
sudo cp ~/coffee_calculator_backup_YYYYMMDD.db /path/to/coffee-calculator/data/coffee_calculator.db
sudo chown your-user:your-user /path/to/coffee-calculator/data/coffee_calculator.db
sudo systemctl restart coffee-calculator
```

**Note:** Updates automatically create timestamped backups in the `data/` directory.

## License

This project is open source and available for personal and commercial use.

## Support

For issues or questions, please check the troubleshooting section or review the code comments in the source files.
