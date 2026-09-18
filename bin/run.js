#!/usr/bin/env node

/**
 * shift-this-version Node.js / npx executable wrapper.
 * 
 * 1. Checks if `uvx` is available (fastest execution with zero config).
 * 2. Checks if `pipx` or `python` is available with `shift-this-version`.
 * 3. Fallback: If no Python is installed on the machine, automatically downloads
 *    the standalone binary for the user's OS from GitHub Releases into local cache
 *    and executes it.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const https = require('https');
const http = require('http');
const { spawn, spawnSync } = require('child_process');

const pkg = require('../package.json');
const VERSION = pkg.version;
const GITHUB_REPO = 'snui1s/shift-this-version';

function commandExists(cmd) {
  try {
    const isWin = process.platform === 'win32';
    const testCmd = isWin ? 'where.exe' : 'which';
    const res = spawnSync(testCmd, [cmd], { stdio: 'ignore' });
    return res.status === 0;
  } catch (e) {
    return false;
  }
}

function runCommand(cmd, args) {
  const child = spawn(cmd, args, { stdio: 'inherit' });
  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code || 0);
    }
  });
  child.on('error', (err) => {
    // If spawning failed, fallback to standalone binary
    fallbackToStandaloneBinary(process.argv.slice(2));
  });
}

function getBinaryName() {
  const platform = process.platform;
  const arch = process.arch;

  if (platform === 'win32') {
    return 'shift-this-version-windows-x64.exe';
  } else if (platform === 'darwin') {
    return arch === 'arm64'
      ? 'shift-this-version-macos-arm64'
      : 'shift-this-version-macos-x64';
  } else if (platform === 'linux') {
    return 'shift-this-version-linux-x64';
  }
  return null;
}

function downloadFile(url, destPath, callback) {
  const client = url.startsWith('https') ? https : http;

  client.get(url, (res) => {
    // Handle redirects (e.g. GitHub Releases redirects to AWS S3)
    if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
      return downloadFile(res.headers.location, destPath, callback);
    }

    if (res.statusCode !== 200) {
      return callback(new Error(`Failed to download binary: HTTP ${res.statusCode} from ${url}`));
    }

    const totalBytes = parseInt(res.headers['content-length'] || '0', 10);
    let downloadedBytes = 0;

    const fileStream = fs.createWriteStream(destPath);
    res.on('data', (chunk) => {
      downloadedBytes += chunk.length;
      if (totalBytes > 0) {
        const percent = Math.round((downloadedBytes / totalBytes) * 100);
        process.stderr.write(`\r[shift-this-version] Downloading standalone binary: ${percent}% (${(downloadedBytes / (1024 * 1024)).toFixed(1)} MB)...`);
      }
    });

    res.pipe(fileStream);

    fileStream.on('finish', () => {
      fileStream.close(() => {
        process.stderr.write('\n');
        callback(null);
      });
    });
  }).on('error', (err) => {
    fs.unlink(destPath, () => {});
    callback(err);
  });
}

function fallbackToStandaloneBinary(userArgs) {
  const binaryName = getBinaryName();
  if (!binaryName) {
    console.error(`[shift-this-version] Unsupported platform: ${process.platform} (${process.arch})`);
    console.error('Please install Python 3.10+ and install via pip: pip install shift-this-version');
    process.exit(1);
  }

  const cacheDir = path.join(os.homedir(), '.shift-this-version', 'bin');
  fs.mkdirSync(cacheDir, { recursive: true });

  const cachedBinary = path.join(cacheDir, `v${VERSION}-${binaryName}`);

  // 1. If already cached, run directly
  if (fs.existsSync(cachedBinary)) {
    return runCommand(cachedBinary, userArgs);
  }

  // 2. Download from GitHub Release
  const downloadUrl = `https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/${binaryName}`;
  console.error(`[shift-this-version] Python not detected. Fetching standalone binary (v${VERSION})...`);

  downloadFile(downloadUrl, cachedBinary, (err) => {
    if (err) {
      console.error(`\n[shift-this-version] Error downloading standalone binary: ${err.message}`);
      console.error('You can install shift-this-version via Python:');
      console.error('  $ pip install shift-this-version');
      console.error('  $ uv tool install shift-this-version\n');
      process.exit(1);
    }

    if (process.platform !== 'win32') {
      try {
        fs.chmodSync(cachedBinary, 0o755);
      } catch (e) {}
    }

    runCommand(cachedBinary, userArgs);
  });
}

function main() {
  const userArgs = process.argv.slice(2);

  // Strategy 1: uvx (fastest, runs modern python tool without touching system python)
  if (commandExists('uvx')) {
    return runCommand('uvx', [`shift-this-version@${VERSION}`, ...userArgs]);
  }

  // Strategy 2: pipx
  if (commandExists('pipx')) {
    return runCommand('pipx', ['run', `shift-this-version@${VERSION}`, ...userArgs]);
  }

  // Strategy 3: Check if shift-this-version is already installed on system PATH
  if (commandExists('shift-this-version')) {
    return runCommand('shift-this-version', userArgs);
  }

  // Strategy 4: Fallback to standalone executable (no Python required)
  fallbackToStandaloneBinary(userArgs);
}

main();
