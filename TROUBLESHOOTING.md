# Troubleshooting CORS Issues

## Quick Checks

### 1. Verify Azure Portal CORS is Saved and App is Restarted
- ✅ Go to Azure Portal → Your App → CORS
- ✅ Confirm `https://lemon-water-065707a1e.4.azurestaticapps.net` is in the list
- ✅ Click **Save** if you haven't already
- ✅ Go to **Overview** → **Restart** → Wait 2-3 minutes
- ✅ Check status shows "Running"

### 2. Check Browser Console for Exact Error
Open browser DevTools (F12) → Console tab → Look for:
- CORS errors (blocked by CORS policy)
- Network errors (failed to fetch)
- Any other error messages

### 3. Check Network Tab
- DevTools → Network tab
- Make a request
- Find the **OPTIONS** request (preflight)
- Click it → **Headers** tab
- Check **Response Headers** for:
  - `Access-Control-Allow-Origin: https://lemon-water-065707a1e.4.azurestaticapps.net`
  - `Access-Control-Allow-Methods: GET, POST, OPTIONS`
  - `Access-Control-Allow-Credentials: true`

If these headers are **missing**, the issue is with Azure or backend deployment.

### 4. Verify Backend is Running
- Test the API directly: https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/
- Should see: "Book Recommendation API is running!"
- If it doesn't load, the backend isn't running

### 5. Check Deployment Status
- Go to GitHub Actions: https://github.com/soungofmusic/BookRecomendation/actions
- Check the latest deployment workflow
- Ensure it completed successfully (green checkmark)

### 6. Clear Browser Cache Completely
- **Chrome/Edge**: 
  - Ctrl+Shift+Delete
  - Select "All time"
  - Check all boxes
  - Clear data
- **Or use Incognito/Private mode** for a clean test

### 7. Test with Simple Request
Open browser console and run:
```javascript
fetch('https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/api/recommend', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'https://lemon-water-065707a1e.4.azurestaticapps.net',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
  }
}).then(r => {
  console.log('Status:', r.status);
  console.log('CORS Headers:', {
    'Access-Control-Allow-Origin': r.headers.get('Access-Control-Allow-Origin'),
    'Access-Control-Allow-Methods': r.headers.get('Access-Control-Allow-Methods'),
    'Access-Control-Allow-Credentials': r.headers.get('Access-Control-Allow-Credentials')
  });
}).catch(e => console.error('Error:', e));
```

Expected result:
- Status: 200
- All CORS headers should be present

## Common Issues

### Issue: Headers are missing in OPTIONS response
**Solution**: Azure Portal CORS configuration or backend deployment issue
- Verify Azure Portal CORS is saved
- Verify backend was restarted after saving
- Check backend deployment completed

### Issue: Headers are present but still getting CORS error
**Possible causes**:
- Origin mismatch (check for typos, trailing slashes)
- Credentials mismatch (should be consistent)
- Browser cache (clear it!)

### Issue: Backend not responding
**Solution**: Check Azure App Service status
- Azure Portal → Your App → Overview
- Status should be "Running"
- If not, click Start

## Still Not Working?

1. **Check Azure Logs**:
   - Azure Portal → Your App → Log stream
   - Look for errors or CORS-related messages

2. **Verify exact origin URL**:
   - Must be: `https://lemon-water-065707a1e.4.azurestaticapps.net`
   - No `http://`, no trailing `/`
   - Case-sensitive

3. **Try temporarily allowing all origins** (testing only):
   - Azure Portal → CORS → Remove your origin
   - Add `*` instead
   - Save and restart
   - If this works, the issue is with the origin URL
   - **Remember to change it back** after testing!

## What's NOT the Issue

- ❌ OpenLibrary API (that's server-side, doesn't affect CORS)
- ❌ Frontend code (it's configured correctly)
- ❌ CSP (Content Security Policy - already fixed)

The issue is either:
- ✅ Azure Portal CORS configuration
- ✅ Backend deployment/restart
- ✅ Browser cache

