# Quick Start Guide

## Installation & Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Compile the Extension**
   ```bash
   npm run compile
   ```

## Running the Extension

### Option 1: Debug Mode (Recommended for Development)
1. Open this folder in VS Code
2. Press `F5` or go to Run > Start Debugging
3. A new VS Code window (Extension Development Host) will open
4. In the new window, press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
5. Type "Open Web Browser" and select the command
6. The web browser panel will open

### Option 2: Package and Install
1. Install vsce (if not already installed):
   ```bash
   npm install -g @vscode/vsce
   ```

2. Package the extension:
   ```bash
   vsce package
   ```

3. Install the generated `.vsix` file:
   - In VS Code, go to Extensions view (`Ctrl+Shift+X`)
   - Click the "..." menu at the top
   - Select "Install from VSIX..."
   - Choose the generated `.vsix` file

## Using the Browser

Once the browser panel opens:

1. **Enter a URL** in the address bar (e.g., `example.com` or `https://github.com`)
   - The `https://` protocol is added automatically if you don't include it

2. **Navigate** using the toolbar buttons:
   - ← Back
   - → Forward
   - ⟳ Refresh

3. **Press Enter** or click **Go** to load the page

## Default Homepage

The browser opens with Google as the default page. You can change this in `src/extension.ts` by modifying line ~180:

```typescript
<input type="text" id="urlInput" placeholder="Enter URL (e.g., https://example.com)" value="https://www.google.com">
```

Change `value="https://www.google.com"` to any URL you prefer.

## Troubleshooting

### Some websites don't load
Some websites (like Google, Facebook) prevent embedding in iframes due to security policies. Try these sites that typically work:
- https://example.com
- https://wikipedia.org
- https://github.com
- https://stackoverflow.com

### Extension doesn't activate
1. Check the Output panel (View > Output)
2. Select "Extension Host" from the dropdown
3. Look for any error messages

### Compilation errors
Run the compile command with verbose output:
```bash
npm run compile -- --verbose
```

## Development Commands

- **Compile**: `npm run compile`
- **Watch mode**: `npm run watch` (auto-recompiles on changes)
- **Lint**: `npm run lint`

## Features

✅ Navigate to any website
✅ Back/Forward navigation
✅ Refresh current page
✅ Browser history
✅ VS Code theme integration
✅ Sandbox security

## Known Limitations

⚠️ Some websites block iframe embedding
⚠️ Single browser instance only (no tabs)
⚠️ Limited download support
⚠️ No browser extensions

## Support

For issues or questions, please refer to the main README.md file.
