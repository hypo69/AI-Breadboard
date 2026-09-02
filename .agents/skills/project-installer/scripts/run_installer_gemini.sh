#!/usr/bin/env bash
#
# Launch interactive AI Breadboard Project Installer using Gemini CLI with gemini-3.1-flash-lite
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$SKILL_DIR")")"

INSTRUCTION_FILE="$SKILL_DIR/INSTALL-INSTRUCTION.md"
if [ ! -f "$INSTRUCTION_FILE" ]; then
    INSTRUCTION_FILE="$PROJECT_ROOT/INSTALL-INSTRUCTION.md"
fi

echo "========================================================="
echo "🤖 Launching Gemini CLI Installer (gemini-3.1-flash-lite)"
echo "========================================================="
echo "Project Root: $PROJECT_ROOT"
echo "Instruction:  $INSTRUCTION_FILE"
echo ""

PROMPT="You are the AI Breadboard Interactive Installer. Read and follow all instructions from '$INSTRUCTION_FILE'. Guide me step by step through installing AI Breadboard, perform pre-flight checks, handle errors, and verify directories and components at the end."

# Execute Gemini CLI with gemini-3.1-flash-lite model
gemini --model "gemini-3.1-flash-lite" --prompt "$PROMPT"
