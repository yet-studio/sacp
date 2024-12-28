# Client API Reference

## Language Server Protocol

```python
from sacp.client.lsp import SACPLanguageServer

class CustomLanguageServer(SACPLanguageServer):
    async def verify_document(self, uri, text):
        # Implement verification
        pass
    
    async def check_compliance(self, uri, text):
        # Implement compliance check
        pass
    
    async def analyze_behavior(self, uri, text):
        # Implement behavior analysis
        pass
```

## VSCode Extension API

```typescript
import * as vscode from 'vscode';
import { LanguageClient } from 'vscode-languageclient/node';

// Create client
const client = new LanguageClient(
    'sacp',
    'SACP Language Server',
    serverOptions,
    clientOptions
);

// Handle verification
async function verify() {
    const result = await client.sendRequest('sacp/verify', {
        uri: document.uri.toString(),
        text: document.getText()
    });
    // Handle result
}

// Handle compliance
async function check() {
    const result = await client.sendRequest('sacp/check', {
        uri: document.uri.toString(),
        text: document.getText()
    });
    // Handle result
}
```

## JetBrains Plugin API

```kotlin
class SACPInspection : LocalInspectionTool() {
    override fun buildVisitor(
        holder: ProblemsHolder,
        isOnTheFly: Boolean
    ): PsiElementVisitor {
        return object : PsiElementVisitor() {
            override fun visitElement(element: PsiElement) {
                // Implement inspection
            }
        }
    }
}
```

## Command Line Interface

```python
from sacp.client.cli import CommandLineInterface

class CustomCLI(CommandLineInterface):
    def verify(self, file_path):
        # Implement verification
        pass
    
    def check(self, file_path):
        # Implement compliance check
        pass
    
    def analyze(self, file_path):
        # Implement behavior analysis
        pass
```

## Integration Examples

1. Language Server
```python
server = SACPLanguageServer()
server.start()
```

2. VSCode Extension
```typescript
export function activate(context: vscode.ExtensionContext) {
    // Initialize client
    const client = new LanguageClient(...);
    client.start();
}
```

3. Command Line
```python
cli = CommandLineInterface()
cli.run(sys.argv[1:])
```
