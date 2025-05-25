#!/bin/bash
# .scripts/update_llm_embeddings.sh

cd ~/Projects/pyNance/
git pull
anythingllm embed ./backend
anythingllm embed ./frontend
