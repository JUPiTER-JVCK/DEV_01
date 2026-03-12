import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('Web Browser extension is now active');

    let disposable = vscode.commands.registerCommand('webBrowser.open', () => {
        BrowserPanel.createOrShow(context.extensionUri);
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}

class BrowserPanel {
    public static currentPanel: BrowserPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _extensionUri: vscode.Uri;
    private _disposables: vscode.Disposable[] = [];

    public static createOrShow(extensionUri: vscode.Uri) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If we already have a panel, show it
        if (BrowserPanel.currentPanel) {
            BrowserPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Otherwise, create a new panel
        const panel = vscode.window.createWebviewPanel(
            'webBrowser',
            'Web Browser',
            column || vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [extensionUri]
            }
        );

        BrowserPanel.currentPanel = new BrowserPanel(panel, extensionUri);
    }

    private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
        this._panel = panel;
        this._extensionUri = extensionUri;

        // Set the webview's initial html content
        this._update();

        // Listen for when the panel is disposed
        // This happens when the user closes the panel or when the panel is closed programmatically
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

        // Handle messages from the webview
        this._panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'alert':
                        vscode.window.showInformationMessage(message.text);
                        return;
                }
            },
            null,
            this._disposables
        );
    }

    public dispose() {
        BrowserPanel.currentPanel = undefined;

        // Clean up our resources
        this._panel.dispose();

        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }

    private _update() {
        const webview = this._panel.webview;
        this._panel.title = 'Web Browser';
        this._panel.webview.html = this._getHtmlForWebview(webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; frame-src https:; style-src 'unsafe-inline'; script-src 'unsafe-inline';">
    <title>Web Browser</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: var(--vscode-font-family);
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .toolbar {
            display: flex;
            gap: 8px;
            padding: 8px;
            background-color: var(--vscode-sideBar-background);
            border-bottom: 1px solid var(--vscode-panel-border);
        }

        #urlInput {
            flex: 1;
            padding: 6px 12px;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            font-size: 14px;
        }

        #urlInput:focus {
            outline: 1px solid var(--vscode-focusBorder);
        }

        button {
            padding: 6px 16px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }

        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        button:active {
            opacity: 0.8;
        }

        #browserFrame {
            flex: 1;
            border: none;
            width: 100%;
            background-color: white;
        }

        .error {
            padding: 20px;
            text-align: center;
            color: var(--vscode-errorForeground);
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <button id="backBtn" title="Go Back">←</button>
        <button id="forwardBtn" title="Go Forward">→</button>
        <button id="refreshBtn" title="Refresh">⟳</button>
        <input type="text" id="urlInput" placeholder="Enter URL (e.g., https://example.com)" value="https://www.google.com">
        <button id="goBtn">Go</button>
    </div>
    <iframe id="browserFrame" sandbox="allow-same-origin allow-scripts allow-popups allow-forms"></iframe>

    <script>
        (function() {
            const urlInput = document.getElementById('urlInput');
            const goBtn = document.getElementById('goBtn');
            const backBtn = document.getElementById('backBtn');
            const forwardBtn = document.getElementById('forwardBtn');
            const refreshBtn = document.getElementById('refreshBtn');
            const browserFrame = document.getElementById('browserFrame');

            let history = [];
            let currentIndex = -1;

            function loadUrl(url) {
                // Ensure the URL has a protocol
                if (!url.startsWith('http://') && !url.startsWith('https://')) {
                    url = 'https://' + url;
                }

                try {
                    browserFrame.src = url;

                    // Add to history if it's a new navigation
                    if (currentIndex === -1 || history[currentIndex] !== url) {
                        history = history.slice(0, currentIndex + 1);
                        history.push(url);
                        currentIndex = history.length - 1;
                    }

                    updateButtons();
                } catch (error) {
                    console.error('Error loading URL:', error);
                }
            }

            function updateButtons() {
                backBtn.disabled = currentIndex <= 0;
                forwardBtn.disabled = currentIndex >= history.length - 1;
            }

            goBtn.addEventListener('click', () => {
                const url = urlInput.value.trim();
                if (url) {
                    loadUrl(url);
                }
            });

            urlInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const url = urlInput.value.trim();
                    if (url) {
                        loadUrl(url);
                    }
                }
            });

            backBtn.addEventListener('click', () => {
                if (currentIndex > 0) {
                    currentIndex--;
                    const url = history[currentIndex];
                    browserFrame.src = url;
                    urlInput.value = url;
                    updateButtons();
                }
            });

            forwardBtn.addEventListener('click', () => {
                if (currentIndex < history.length - 1) {
                    currentIndex++;
                    const url = history[currentIndex];
                    browserFrame.src = url;
                    urlInput.value = url;
                    updateButtons();
                }
            });

            refreshBtn.addEventListener('click', () => {
                browserFrame.src = browserFrame.src;
            });

            // Load initial URL
            loadUrl(urlInput.value);
        })();
    </script>
</body>
</html>`;
    }
}
