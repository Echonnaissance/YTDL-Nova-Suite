# Browser Setup Guide for Cookie Authentication

This guide explains how to configure browser cookies for downloading from platforms that require authentication (Twitter/X, Instagram, etc.).

## Supported Browsers

The following browsers are fully supported:

- **Chrome** - `chrome`
- **Brave** - `brave` ✅ **Recommended if Brave is your main browser**
- **Firefox** - `firefox`
- **Edge** - `edge`
- **Opera** - `opera`
- **Chromium** - `chromium`
- **Safari** - `safari`

## Browser-Specific Notes

### Brave Browser

**Status**: ✅ **Supported (with important caveat)**

Brave is Chromium-based, so yt-dlp can access its cookies the same way as Chrome. However, **Brave locks its cookie database while running**, which requires a workaround.

**Configuration:**

```bash
# Standalone script
python UMDConverter.py <URL> --cookies-browser brave

# Backend (.env file)
COOKIE_BROWSER=brave
```

**⚠️ IMPORTANT - Cookie Database Lock Issue:**

- Brave locks its cookie database file while the browser is running
- yt-dlp needs to copy this database, which fails if Brave is open
- **Solution: Close Brave completely before running downloads**

**Why this happens:**

- Brave stores cookies in the same format as Chrome/Chromium
- yt-dlp needs to copy the cookie database to a temporary location
- Windows file locking prevents this copy while Brave is running

**Workarounds:**

1. **Close Brave** before downloading (recommended)
2. Use Firefox instead (Firefox doesn't have this issue)
3. Export cookies manually and use `--cookies` option (advanced)

### Firefox with Tor Integration

**Status**: ✅ **Works Normally**

If you're using regular Firefox with Tor proxy configured (via add-ons or manual proxy settings), it works exactly like regular Firefox.

**Configuration:**

```bash
# Standalone script
python UMDConverter.py <URL> --cookies-browser firefox

# Backend (.env file)
COOKIE_BROWSER=firefox
```

**How it works:**

- The Tor proxy routing doesn't affect cookie storage
- Cookies are stored in Firefox's normal cookie database
- yt-dlp accesses cookies the same way as regular Firefox
- The proxy only affects network routing, not cookie access

**Note**: If you're using the actual **Tor Browser** (the modified Firefox bundle), you can still use `firefox`, but:

- Tor Browser has enhanced privacy settings that may limit cookie access
- Some cookies might be cleared when you close Tor Browser
- If downloads fail, try using Brave or regular Firefox instead

## Quick Setup

### For Standalone Script

**Using Brave (Recommended):**

```bash
python UMDConverter.py https://x.com/user/status/123456 --cookies-browser brave
```

**Using Firefox with Tor:**

```bash
python UMDConverter.py https://x.com/user/status/123456 --cookies-browser firefox
```

### For Backend (Web App)

**1. Edit `backend/.env` file:**

```env
COOKIE_BROWSER=brave
```

**2. Restart the backend server**

**3. The web app will automatically use Brave cookies for all downloads**

### Using Configuration File

**Create `config.json`:**

```json
{
  "url": "https://x.com/user/status/123456",
  "cookies_browser": "brave",
  "output_dir": "Downloads/Video"
}
```

**Run:**

```bash
python UMDConverter.py --config config.json
```

## Troubleshooting

### "Could not copy Chrome cookie database" Error

**This error occurs with Brave (and sometimes Chrome) when the browser is running.**

**Cause:**

- Brave/Chrome locks its cookie database file while running
- yt-dlp cannot copy the locked database file

**Solutions:**

1. **Close Brave completely** (check Task Manager to ensure all Brave processes are closed)
2. Run the download command again
3. If you need to keep browsing, use Firefox instead: `--cookies-browser firefox`

### "No cookies found" Error

**Possible causes:**

1. Browser is not logged into the platform (Twitter/X, Instagram, etc.)
2. Cookies were cleared recently
3. Browser was closed when cookies were needed (for Firefox)

**Solutions:**

1. Open your browser and log into the platform
2. For Firefox: Keep the browser open (or at least logged in) when downloading
3. For Brave: Close the browser before downloading (see above)
4. Try a different browser if one doesn't work

### Tor Browser Issues

If you're using Tor Browser and downloads fail:

- Try using `firefox` as the browser option
- If that doesn't work, use Brave or regular Firefox instead
- Tor Browser's privacy settings may prevent cookie access

### Firefox with Tor Proxy

If Firefox with Tor proxy isn't working:

- Make sure you're logged into the platform in Firefox
- The Tor proxy shouldn't affect cookie access, but try regular Firefox mode
- Check that Firefox isn't in private/incognito mode

## Recommendations

**For your setup (Brave + Firefox with Tor):**

1. **Primary choice: Brave** ✅

   - Since Brave is your main browser, use `--cookies-browser brave`
   - Most reliable option
   - Cookies are always available

2. **Secondary choice: Firefox**

   - Use `--cookies-browser firefox` if you prefer Firefox
   - Works fine even with Tor proxy configured
   - Make sure you're logged into platforms in Firefox

3. **Configuration:**
   - Set `COOKIE_BROWSER=brave` in `backend/.env` for the web app
   - Use `--cookies-browser brave` for standalone script
   - Update `config.json` with `"cookies_browser": "brave"`

## Testing

To test if cookies are working:

```bash
# Test with a Twitter/X URL
python UMDConverter.py https://x.com/user/status/123456 --cookies-browser brave --verbose

# If it works, you'll see the download start
# If it fails with authentication errors, check that you're logged into Twitter/X in Brave
```

## Security Notes

- Cookies are read from your browser's cookie database
- No cookies are modified or sent anywhere except to the target platform
- The downloader only reads cookies, never writes them
- Your browser's security settings still apply

---

**Need help?** Check the main README.md or open an issue on GitHub.
