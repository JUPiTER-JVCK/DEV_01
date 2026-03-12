# VS Code Web Browser Extension

A simple web browser extension for Visual Studio Code that allows you to browse websites directly within the editor.

## Features

- Browse websites inside VS Code
- Navigation controls (back, forward, refresh)
- URL input with auto-completion (adds https:// prefix if missing)
- Browser history navigation
- Clean, integrated UI that follows VS Code's theme

## Installation

### From Source

1. Clone this repository
2. Open the folder in VS Code
3. Run `npm install` to install dependencies
4. Run `npm run compile` to compile the TypeScript code
5. Press F5 to launch the Extension Development Host

### Manual Installation

1. Run `npm install` to install dependencies
2. Run `npm run compile` to compile the extension
3. Package the extension: `vsce package` (requires vsce: `npm install -g @vscode/vsce`)
4. Install the generated `.vsix` file in VS Code

## Usage

1. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on Mac)
2. Type "Open Web Browser" and select the command
3. A new panel will open with a web browser
4. Enter a URL in the address bar and press Enter or click "Go"

### Navigation

- **Back button (←)**: Navigate to the previous page
- **Forward button (→)**: Navigate to the next page
- **Refresh button (⟳)**: Reload the current page
- **URL bar**: Enter any website URL (protocol is optional - https:// will be added automatically)

## Default Page

The browser opens with Google as the default homepage. You can change this by modifying the `value` attribute of the URL input in the extension code.

## Security

The browser uses an iframe with sandbox attributes to provide a safe browsing experience:
- `allow-same-origin`: Allows content to maintain its origin
- `allow-scripts`: Allows JavaScript execution
- `allow-popups`: Allows popups
- `allow-forms`: Allows form submission

**Note**: Some websites may not load due to X-Frame-Options or Content Security Policy restrictions that prevent embedding in iframes.

## Development

### Build

```bash
npm run compile
```

### Watch Mode

```bash
npm run watch
```

### Lint

```bash
npm run lint
```

## Requirements

- Visual Studio Code 1.60.0 or higher
- Node.js and npm

## Known Limitations

- Some websites (like Google, Facebook, etc.) may not display properly due to iframe embedding restrictions
- No support for multiple tabs (only one browser instance at a time)
- Limited support for file downloads
- No support for browser extensions or plugins

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT
