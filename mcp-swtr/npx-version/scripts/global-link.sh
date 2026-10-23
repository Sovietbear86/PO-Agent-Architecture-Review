#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BUNDLE="$PROJECT_DIR/dist/index.js"
CMD_NAME="mcp-swtr"

cd "$PROJECT_DIR"

# 1. Сборка (если ещё не или устарел)
if [ ! -f "$BUNDLE" ] || [ "src/index.ts" -nt "$BUNDLE" ]; then
    echo "→ Build: npm run build"
    npm run build
fi

# 2. Целевая bin-директория
detect_bin_dir() {
    # Приоритет: ~/.local/bin → ~/bin → /usr/local/bin
    for d in "$HOME/.local/bin" "$HOME/bin" "/usr/local/bin"; do
        if [ -d "$d" ]; then
            echo "$d"
            return
        fi
    done
    # Ни одна не существует — создаём ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    echo "$HOME/.local/bin"
}

BIN_DIR="$(detect_bin_dir)"
TARGET="$BIN_DIR/$CMD_NAME"

# 3. Проверка: не занято ли другим файлом
if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
    echo "ERROR: $TARGET exists and is not a symlink. Remove it manually." >&2
    exit 1
fi

# 4. Симлинк
ln -sf "$BUNDLE" "$TARGET"
chmod +x "$TARGET"

echo "✓ Linked: $TARGET → $BUNDLE"

# 5. Проверка PATH
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "⚠  Warning: $BIN_DIR is not in \$PATH. Add it:"
       echo "   export PATH=\"\$PATH:$BIN_DIR\"" ;;
esac

echo ""
echo "Run: $CMD_NAME"
echo "Unlink: rm \"$TARGET\""
