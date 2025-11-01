# Azure App Service CORS Configuration

If CORS errors persist after deploying the code changes, you may need to configure CORS at the Azure App Service level. Azure App Service has its own CORS settings that can override or interfere with application-level CORS headers.

## Steps to Configure CORS in Azure Portal

1. **Login to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your Azure account

2. **Navigate to Your App Service**
   - Search for "book-recommender-api" in the search bar
   - Click on your App Service resource

3. **Open CORS Settings**
   - In the left sidebar, scroll down to **API** section
   - Click on **CORS** (or search for "CORS" in the search bar)

4. **Configure Allowed Origins**
   - Under "Allowed Origins", click **Add** or use the text box
   - Add your frontend URL: `https://lemon-water-065707a1e.4.azurestaticapps.net`
   - **Important**: Make sure there are no trailing slashes
   - If you want to allow all origins for testing (NOT recommended for production), you can use `*`, but this is less secure

5. **Configure Allowed Methods**
   - Make sure **POST** and **OPTIONS** are checked
   - Also check **GET** if needed

6. **Save Configuration**
   - Click **Save** at the top of the page
   - Wait for the confirmation message

7. **Restart the App Service**
   - In the left sidebar, click **Overview**
   - Click **Restart** button at the top
   - Confirm the restart
   - Wait for the app to restart (usually 1-2 minutes)

## Alternative: Using Azure CLI

If you prefer using command line:

```bash
# Login to Azure
az login

# Configure CORS for your App Service
az webapp cors add \
  --name book-recommender-api \
  --resource-group <your-resource-group> \
  --allowed-origins https://lemon-water-065707a1e.4.azurestaticapps.net

# Restart the app
az webapp restart \
  --name book-recommender-api \
  --resource-group <your-resource-group>
```

## Verify CORS Configuration

After configuring CORS in Azure:

1. **Test the OPTIONS Request**
   - Open browser DevTools → Network tab
   - Try making a request from your frontend
   - Look for the OPTIONS request
   - Check that it returns status 200
   - Verify the response headers include:
     - `Access-Control-Allow-Origin: https://lemon-water-065707a1e.4.azurestaticapps.net`
     - `Access-Control-Allow-Methods: GET, POST, OPTIONS`
     - `Access-Control-Allow-Headers: Content-Type, Accept, Authorization`

2. **Check Application Logs**
   - In Azure Portal → Your App Service → Log stream
   - Monitor logs while making requests
   - Look for any CORS-related errors

## Troubleshooting

### Issue: CORS still not working after Azure configuration

1. **Clear Browser Cache**: Sometimes browsers cache CORS responses
2. **Check for Typos**: Ensure the origin URL matches exactly (no trailing slashes, correct protocol)
3. **Verify Both Configurations**: Both Azure CORS and Flask-CORS should allow the origin
4. **Check Logs**: Look at Azure App Service logs for any errors

### Issue: Conflicting CORS Headers

If you see multiple `Access-Control-Allow-Origin` headers, Azure CORS might be conflicting with Flask-CORS. In this case:
- Either disable Azure CORS and use only Flask-CORS
- Or disable Flask-CORS and use only Azure CORS

For now, it's recommended to configure both (they should work together, but Azure CORS takes precedence).

## Current Status

✅ Code-level CORS configured in `backend/app.py`
⏳ Azure Portal CORS configuration needed (follow steps above)

After completing the Azure Portal configuration, the CORS errors should be resolved.

