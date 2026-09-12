#!/usr/bin/env bash
set -e

echo "🦙 Setting up local Ollama models for Chaos Engineering Lab..."

models=(
    "qwen2.5:3b"
    "qwen3:1.7b"
    "llama3.2:1b"
    "qwen2.5vl:3b"
    "nomic-embed-text"
)

for model in "${models[@]}"; do
    echo "Pulling $model..."
    ollama pull "$model"
done

echo "✅ Ollama environment ready! List of installed models:"
ollama list
