# Product Manager's Guide: Managing Maintenance Mode

This guide explains how to enable and disable the Scheduled Maintenance screen for the Stationery Junction website and mobile app.

---

## 💻 Local Development & Testing (Your Computer)

We have created two simple, double-clickable files in the root folder (`c:\Ecommerce app`) so you don't need to run terminal commands:

### To Turn ON Maintenance Mode:
1. Open the [c:\Ecommerce app](file:///c:/Ecommerce%20app) folder on your computer.
2. Double-click the file named **`enable-maintenance.bat`**.
3. A terminal window will open, activate maintenance mode in `.env`, restart the backend server automatically, and display `Backend API Server started successfully!`.
4. Press any key to close the terminal.

### To Turn OFF Maintenance Mode (Resume Normal Service):
1. Open the [c:\Ecommerce app](file:///c:/Ecommerce%20app) folder.
2. Double-click the file named **`disable-maintenance.bat`**.
3. The terminal window will open, set the flag back to normal, restart the server, and display `Backend API Server started successfully!`.
4. Press any key to close the terminal.

---

## 🌐 Production Server (Live Website & App)

When you deploy to production, you will use one of these two scenarios depending on your hosting setup:

### Scenario A: Running on a VPS/Linux Server (Docker Compose)
If your developer logs into a server command-line terminal to manage your site:
1. Connect/SSH to your production server.
2. Open the `.env` file inside the `backend` folder and change the setting:
   ```env
   MAINTENANCE_MODE=true
   ```
3. Run this single command to apply the change (takes only 3 seconds and does not take down the frontend):
   ```bash
   docker-compose restart backend
   ```
4. To turn it off, change the `.env` file setting back to `false` and restart the backend:
   ```bash
   docker-compose restart backend
   ```

### Scenario B: Running on a Cloud Dashboard (Render, AWS, Heroku, OCI, etc.)
If you manage your production servers through a web browser panel without writing commands:
1. Log into your **Cloud Provider Dashboard** (e.g., Render, AWS, Heroku).
2. Go to your **Backend Service / API Container** details.
3. Locate the **Environment Variables** (or *Config Vars* / *Secrets*) section.
4. Edit the value of the `MAINTENANCE_MODE` variable:
   * Change it to `true` (to turn on maintenance).
   * Change it to `false` (to turn off maintenance).
5. Click **Save** or **Apply Changes**. The hosting provider will automatically restart the backend container to apply the settings.

---

## ✏️ Customizing the Maintenance Message
If you want to edit the paragraphs shown to users on the maintenance screen:

1. Open the file [backend/app/config/maintenance.py](file:///c:/Ecommerce%20app/backend/app/config/maintenance.py) in any text editor.
2. Modify the sentences inside the `MAINTENANCE_MESSAGE_PARAGRAPHS` list:
   ```python
   MAINTENANCE_MESSAGE_PARAGRAPHS = [
       "Stationery Junction is upgrading our database to provide a faster experience.",
       "We will be temporarily offline from 10:00 PM to 11:30 PM IST.",
       "Thank you for your patience!"
   ]
   ```
3. Save the file and restart your backend server.
