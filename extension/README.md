# Chrome/Edge Extension (MV3) – AI Browser Agent

## Files
- `manifest.json`
- `background.js`
- `content_script.js`
- `sidepanel.html`
- `sidepanel.js`

## Load unpacked extension
1. Open Chrome/Edge extensions page.
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
2. Enable **Developer mode**.
3. Click **Load unpacked**.
4. Select the `extension/` folder.
5. Pin and click the extension icon to open the side panel.

## Backend setup
1. Start backend API:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Ensure API URL in side panel is set to:
   `http://localhost:8000/api/tasks/run`

## Usage
1. Open any tab.
2. In side panel, enter a task.
3. Click **Run Task**.
4. The extension sends:
   - `task`
   - `current_page` (sanitized title/links/buttons/inputs/summary)
   - `debug: true`
5. Results show per-step status, logs, and screenshot paths.

## Security notes
- Content script does **not** collect input values.
- Sensitive input fields (password/token/card-like fields) are filtered out.
- Backend safety blocking still applies for login/payment/form-submission style tasks.
