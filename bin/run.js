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
const crypto = require('crypto');
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

function runCommand(cmd, args, isStandalone = false) {
  const child = spawn(cmd, args, { stdio: 'inherit' });
  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code || 0);
    }
  });
  child.on('error', (err) => {
    // If spawning failed, fallback to standalone binary (but never loop on the binary itself)
    if (isStandalone) {
      console.error(`[shift-this-version] Failed to run standalone binary: ${err.message}`);
      process.exit(1);
    }
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

function fetchText(url, callback, redirects = 0) {
  if (redirects > 5) return callback(new Error('Too many redirects'));
  const client = url.startsWith('https') ? https : http;
  client.get(url, (res) => {
    if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
      res.resume();
      return fetchText(res.headers.location, callback, redirects + 1);
    }
    if (res.statusCode !== 200) {
      res.resume();
      return callback(new Error(`HTTP ${res.statusCode} from ${url}`));
    }
    let body = '';
    res.setEncoding('utf8');
    res.on('data', (c) => { body += c; });
    res.on('end', () => callback(null, body));
  }).on('error', callback);
}

function sha256File(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
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

  // 1. If already cached (only verified binaries are ever moved here), run directly
  if (fs.existsSync(cachedBinary)) {
    return runCommand(cachedBinary, userArgs, true);
  }

  // 2. Download from GitHub Release and verify its published SHA256 before use
  const downloadUrl = `https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/${binaryName}`;
  const tmpBinary = `${cachedBinary}.part`;
  console.error(`[shift-this-version] Python not detected. Fetching standalone binary (v${VERSION})...`);

  const fail = (err) => {
    fs.unlink(tmpBinary, () => {});
    console.error(`\n[shift-this-version] Error downloading standalone binary: ${err.message}`);
    console.error('You can install shift-this-version via Python:');
    console.error('  $ pip install shift-this-version');
    console.error('  $ uv tool install shift-this-version\n');
    process.exit(1);
  };

  fetchText(`${downloadUrl}.sha256`, (sumErr, sumText) => {
    if (sumErr) return fail(new Error(`Could not fetch checksum (${sumErr.message}); refusing to run unverified binary`));
    const expected = (sumText || '').trim().split(/\s+/)[0].toLowerCase();
    if (!/^[0-9a-f]{64}$/.test(expected)) return fail(new Error('Invalid checksum file; refusing to run unverified binary'));

    downloadFile(downloadUrl, tmpBinary, (err) => {
      if (err) return fail(err);

      const actual = sha256File(tmpBinary);
      if (actual !== expected) {
        return fail(new Error(`SHA256 mismatch (expected ${expected}, got ${actual}); binary discarded`));
      }

      if (process.platform !== 'win32') {
        try {
          fs.chmodSync(tmpBinary, 0o755);
        } catch (e) {}
      }
      fs.renameSync(tmpBinary, cachedBinary);
      runCommand(cachedBinary, userArgs, true);
    });
  });
}

function main() {
  const userArgs = process.argv.slice(2);

  // Fast-path: --version, -v, or --v
  if (userArgs.length === 1 && (userArgs[0] === '--version' || userArgs[0] === '-v' || userArgs[0] === '--v')) {
    console.log(`shift-this-version ${VERSION}`);
    return;
  }

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
