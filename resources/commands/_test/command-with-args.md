# Command With Args

A test command that accepts arguments to test argument pattern handling.

## Arguments

- `target`: The target to operate on (required)
- `--verbose`: Enable verbose output (optional flag)
- `--format <type>`: Output format - json, text, or yaml (optional, default: text)

## Instructions

When this command is invoked with arguments:
1. Parse and validate the provided arguments
2. Report which arguments were received
3. Echo back the target value
4. If --verbose is set, provide detailed output
5. Format the response according to --format if specified
