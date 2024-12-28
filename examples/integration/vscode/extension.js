/**
 * Example VSCode extension integration with SACP
 */

const vscode = require('vscode');
const { LanguageClient } = require('vscode-languageclient/node');

let client;

/**
 * Activate the extension
 */
function activate(context) {
    // Initialize SACP client
    const serverOptions = {
        command: 'sacp',
        args: ['serve', '--lsp']
    };

    const clientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'python' },
            { scheme: 'file', language: 'javascript' },
            { scheme: 'file', language: 'typescript' }
        ],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{py,js,ts}')
        }
    };

    // Create language client
    client = new LanguageClient(
        'sacp',
        'SACP Language Server',
        serverOptions,
        clientOptions
    );

    // Start client
    client.start();

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sacp.verify', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            try {
                const result = await client.sendRequest('sacp/verify', {
                    uri: editor.document.uri.toString(),
                    text: editor.document.getText()
                });

                // Show results in custom view
                vscode.window.createWebviewPanel(
                    'sacpResults',
                    'SACP Verification Results',
                    vscode.ViewColumn.Two,
                    {}
                ).webview.html = formatResults(result);
            } catch (error) {
                vscode.window.showErrorMessage(`SACP verification failed: ${error.message}`);
            }
        }),

        vscode.commands.registerCommand('sacp.check', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            try {
                const result = await client.sendRequest('sacp/check', {
                    uri: editor.document.uri.toString(),
                    text: editor.document.getText()
                });

                // Show results
                showComplianceResults(result);
            } catch (error) {
                vscode.window.showErrorMessage(`SACP compliance check failed: ${error.message}`);
            }
        })
    );
}

/**
 * Deactivate the extension
 */
function deactivate() {
    if (client) {
        return client.stop();
    }
}

/**
 * Format verification results as HTML
 */
function formatResults(results) {
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .violation { color: #d73a49; }
                .warning { color: #e36209; }
                .info { color: #005cc5; }
            </style>
        </head>
        <body>
            <h2>SACP Verification Results</h2>
            ${results.violations.map(v => `
                <div class="violation">
                    <h3>❌ ${v.property}</h3>
                    <p>${v.description}</p>
                    <pre>${v.context}</pre>
                </div>
            `).join('')}
            ${results.warnings.map(w => `
                <div class="warning">
                    <h3>⚠️ ${w.property}</h3>
                    <p>${w.description}</p>
                    <pre>${w.context}</pre>
                </div>
            `).join('')}
        </body>
        </html>
    `;
}

/**
 * Show compliance check results
 */
function showComplianceResults(results) {
    const panel = vscode.window.createWebviewPanel(
        'sacpCompliance',
        'SACP Compliance Results',
        vscode.ViewColumn.Two,
        {}
    );

    panel.webview.html = `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .rule { margin-bottom: 20px; }
                .pass { color: #28a745; }
                .fail { color: #d73a49; }
            </style>
        </head>
        <body>
            <h2>SACP Compliance Results</h2>
            ${Object.entries(results.rules).map(([rule, result]) => `
                <div class="rule ${result.passed ? 'pass' : 'fail'}">
                    <h3>${result.passed ? '✅' : '❌'} ${rule}</h3>
                    <p>${result.description}</p>
                    ${result.passed ? '' : `
                        <pre>${result.context}</pre>
                        <p>Suggestion: ${result.suggestion}</p>
                    `}
                </div>
            `).join('')}
        </body>
        </html>
    `;
}

module.exports = {
    activate,
    deactivate
};
