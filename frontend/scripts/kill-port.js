const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

try {
  const port = 3000;
  console.log(`[Port-Killer] Checking for active processes on port ${port}...`);
  
  if (process.platform === 'win32') {
    // Windows: Use netstat to find PID and taskkill to terminate it
    const stdout = execSync(`netstat -ano | findstr :${port}`).toString();
    const lines = stdout.split('\n').filter(line => line.includes('LISTENING'));
    
    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      const pid = parts[parts.length - 1];
      if (pid && pid !== '0') {
        console.log(`[Port-Killer] Found stale process PID ${pid} occupying port ${port}. Terminating...`);
        execSync(`taskkill /F /PID ${pid}`);
      }
    }
  } else {
    // UNIX (Mac/Linux): Use lsof and kill
    try {
      const pids = execSync(`lsof -t -i:${port}`).toString().trim().split('\n');
      for (const pid of pids) {
        if (pid) {
          console.log(`[Port-Killer] Found stale process PID ${pid} occupying port ${port}. Terminating...`);
          execSync(`kill -9 ${pid}`);
        }
      }
    } catch (_) {
      // lsof returns exit code 1 if no processes are found
    }
  }
} catch (e: any) { console.warn("Background task failed", e); }
console.log('[Port-Killer] Port 3000 is clean and ready.');

// Clean the .next build directory to prevent development and production config cache conflicts
try {
  const nextDir = path.join(__dirname, '..', '.next');
  if (fs.existsSync(nextDir)) {
    console.log('[Port-Killer] Cleaning stale build files in .next...');
    fs.rmSync(nextDir, { recursive: true, force: true });
    console.log('[Port-Killer] .next folder cleaned successfully.');
  }
} catch (error) {
  console.log('[Port-Killer] Warning: Failed to clean .next folder:', error.message);
}

// Clean the node_modules/.cache directory to prevent Webpack persistent cache mismatches
try {
  const cacheDir = path.join(__dirname, '..', 'node_modules', '.cache');
  if (fs.existsSync(cacheDir)) {
    console.log('[Port-Killer] Cleaning compiler cache in node_modules/.cache...');
    fs.rmSync(cacheDir, { recursive: true, force: true });
    console.log('[Port-Killer] Cache folder cleaned successfully.');
  }
} catch (error) {
  console.log('[Port-Killer] Warning: Failed to clean cache folder:', error.message);
}
