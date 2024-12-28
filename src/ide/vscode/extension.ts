import * as path from 'path';
import * as vscode from 'vscode';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    // Server options - use Python executable
    const serverModule = context.asAbsolutePath(
        path.join('src', 'ide', 'lsp_server.py')
    );
    
    const serverOptions: ServerOptions = {
        run: {
            command: 'python',
            args: [serverModule],
            transport: TransportKind.stdio
        },
        debug: {
            command: 'python',
            args: ['-m', 'debugpy', '--listen', '5678', serverModule],
            transport: TransportKind.stdio
        }
    };

    // Client options
    const clientOptions: LanguageClientOptions = {
        documentSelector: [
            { scheme: 'file', language: 'python' }
        ],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.py')
        }
    };

    // Create and start client
    client = new LanguageClient(
        'sacp',
        'SACP Language Server',
        serverOptions,
        clientOptions
    );

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('sacp.verify', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                await client.sendRequest('workspace/executeCommand', {
                    command: 'sacp.verify',
                    arguments: [{ uri: editor.document.uri.toString() }]
                });
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sacp.checkCompliance', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                await client.sendRequest('workspace/executeCommand', {
                    command: 'sacp.checkCompliance',
                    arguments: [{ uri: editor.document.uri.toString() }]
                });
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('sacp.analyzeBehavior', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                await client.sendRequest('workspace/executeCommand', {
                    command: 'sacp.analyzeBehavior',
                    arguments: [{ uri: editor.document.uri.toString() }]
                });
            }
        })
    );

    // Start the client
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
