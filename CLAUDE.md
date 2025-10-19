# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a VS Code extension called "Code2Pseudocode & Flowchart Generator" that converts Python code into pseudocode and generates interactive flowcharts using Mermaid. The extension provides bidirectional navigation between Python source code, pseudocode, and flowchart nodes.

## Common Development Commands

### Building and Testing
```bash
# Compile TypeScript and bundle with webpack
npm run compile

# Watch mode for development (rebuilds on file changes)
npm run watch

# Build production bundle (minified with source maps)
npm run package

# Run tests
npm test

# Type checking without emitting files
npm run check-types

# Run linter
npm run lint
```

### Development Workflow
1. Use `npm run watch` during development for automatic rebuilds
2. Press F5 in VS Code to launch the extension in a new Extension Development Host window
3. Test with Python files using the context menu commands or command palette

## Architecture Overview

### Core Data Flow

The extension follows this processing pipeline:

1. **Python Analysis** → `pythonAnalyzer.ts` uses Python's AST module via subprocess to parse Python code
2. **Flowchart Generation** → AST visitor generates Mermaid flowchart code with node metadata
3. **WebView Display** → `extension.ts` creates a webview panel displaying the flowchart using `media/flowview.html`
4. **Pseudocode Generation** → `claudeApi.ts` calls Claude API to convert Python to pseudocode (on-demand)
5. **Bidirectional Linking** → `WebviewEventHandler.ts` manages synchronization between editor, flowchart, and pseudocode

### Key Architectural Components

#### 1. Mapping System (Critical)
The extension maintains three critical mapping structures exported from `extension.ts`:

- **`lineToNodeMap`**: Maps Python line numbers → flowchart node IDs (1:many)
- **`pseudocodeToLineMap`**: Maps pseudocode line numbers → Python line numbers (1:1)
- **`nodeIdToLine`**: Maps flowchart node IDs → Python line numbers (1:1)

These mappings enable the core feature of clicking/selecting in any view (editor/flowchart/pseudocode) and highlighting corresponding elements in all other views.

#### 2. Python AST Processing (`pythonAnalyzer.ts`)
This module generates Python code dynamically that:
- Defines a `FlowchartGenerator` class (AST visitor pattern)
- Processes Python code through multiple visitor methods (`visit_If`, `visit_For`, `visit_While`, etc.)
- Handles complex control flow including nested structures, break/continue, and multiple branches
- Returns JSON-formatted output: Mermaid code, line mappings, node sequence, and node metadata

The Python script is written to a temp file and executed via subprocess to avoid command-line length limits on Windows.

#### 3. WebView Communication (`WebviewEventHandler.ts`)
Handles bidirectional messages between the extension and webview:

**From WebView → Extension:**
- `webview.FlowchartNodeClicked`: User clicked a flowchart node
- `webview.pseudocodeLineClicked`: User clicked a pseudocode line (single)
- `webview.pseudocodeLinesClicked`: User clicked/selected multiple pseudocode lines
- `webview.requestClearEditor`: Request to clear editor highlights
- `webview.clearPseudocodeHistory`: Clear cached pseudocode

**From Extension → WebView:**
- `updatePseudocode`: Send new pseudocode text
- `setLineMapping`: Send line mapping data
- `highlightNodesAndPseudocode`: Highlight specific nodes and lines
- `clearHighlight`: Clear all highlights

#### 4. Claude API Integration (`claudeApi.ts`)
- Uses Claude Sonnet 4 to convert full Python code to pseudocode
- Implements `buildLineMapping()` heuristic to align Python and pseudocode lines
- Requires `CLAUDE_API_KEY` environment variable (loaded from `.env`)
- Pseudocode generation is triggered manually via "Convert to Pseudocode" command
- Results are cached until code changes

### State Management

#### Extension-Level State (`extension.ts`)
- `sourceDocUri`: Tracks which document generated the current flowchart
- `currentPanel`: Reference to active webview panel (singleton)
- `pseudocodeHistory`: Stores generated pseudocode for display
- `pseudocodeCache`: Caches pseudocode by code content
- `fullPseudocodeGenerated`: Flag indicating whether complete pseudocode mapping exists

#### Editor Decorations
- `highlightDecorationType` in `WebviewEventHandler.ts` provides visual highlighting
- Highlights are applied/cleared based on user interactions across all views

### Event-Driven Synchronization

The extension uses VS Code's `onDidChangeTextEditorSelection` to automatically highlight corresponding flowchart nodes and pseudocode lines when the user:
- Moves cursor to a new line
- Selects multiple lines

This creates a seamless "live linking" experience between code and visualization.

## Important Implementation Details

### Python Subprocess Execution
- Extension tries multiple Python commands in order: `python3`, `python`, `py`
- Uses `-X utf8` flag for proper encoding on Windows
- Temporary files are created in `os.tmpdir()` to avoid command-line limitations
- Output is parsed by splitting on delimiter strings: `---LINE_MAPPING---`, `---NODE_SEQUENCE---`, `---NODE_META---`

### Multi-Selection Support
The extension supports selecting multiple lines in any view:
- **Editor Selection** → Highlights all related flowchart nodes and pseudocode lines
- **Pseudocode Selection** → Implemented via `handlePseudocodeLinesClick()` in `extension.ts`

### Cache Invalidation
Pseudocode cache is cleared when:
- Document content changes (via `onDidChangeTextDocument`)
- User explicitly clears history (command: `code2pseudocode.clearHistory`)

### Environment Setup
A `.env` file in the extension root must contain:
```
CLAUDE_API_KEY=your_api_key_here
```

This is loaded via `dotenv` in the `activate()` function.

## File Structure

```
src/
├── extension.ts              # Main entry point, command registration, state management
├── WebviewEventHandler.ts    # Webview ↔ Extension message handling
├── pythonAnalyzer.ts         # Python AST → Mermaid flowchart generation
├── claudeApi.ts              # Claude API integration for pseudocode
├── codeBlockParser.ts        # Utility for parsing Python code blocks (currently unused)
└── test/
    └── extension.test.ts     # Extension tests

media/
└── flowview.html             # Webview HTML template with Mermaid rendering

dist/                         # Webpack output directory
```

## Extension Commands

- `m5-test2.generate`: Generate Flowchart (WebView) - Main command
- `code2pseudocode.convertToPseudocode`: Convert to Pseudocode
- `code2pseudocode.clearHistory`: Clear pseudocode history

## Common Gotchas

1. **`sourceDocUri` Stale Reference**: If user switches files after generating flowchart, `sourceDocUri` may point to wrong file. The extension checks for this in event handlers.

2. **Pseudocode Mapping Timing**: Users must run "Convert to Pseudocode" *after* generating the flowchart for pseudocode-to-code navigation to work. The extension warns if mapping is not available.

3. **Python Not Found**: If no Python interpreter is in PATH, the extension will fail to generate flowcharts. All three commands (`python3`, `python`, `py`) are tried.

4. **WebView Lifecycle**: When webview is disposed, all mapping state is cleared. Regenerating flowchart recreates all mappings from scratch.

5. **Branch Merging in Flowcharts**: The AST visitor uses `branch_ends` array to track multiple control flow paths that need to converge. This is complex logic in `visit_If`, `visit_For`, and `visit_While`.

## Testing Considerations

When modifying this extension:
- Test with Python files containing nested control structures (if/else, loops)
- Verify mappings work for multi-line statements and function definitions
- Check that highlights clear correctly when switching between different Python files
- Test with code containing Unicode characters (Chinese comments work due to UTF-8 handling)
- Verify that break/continue statements inside loops create correct flowchart paths
