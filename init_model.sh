#!/bin/bash
echo "Initializing Fine-Tuned Reasoning Model..."

# 1. Start services
echo "Starting Academic Buddy System..."
docker compose up -d --build

# 2. Wait a few seconds for Ollama to wake up
sleep 5

# 3. Create the model inside the running Ollama container
echo "Pulling 'granite4-micro' inside the container..."
docker exec -it llm ollama pull granite4:latest

echo "SUCCESS! The system is live at http://localhost:8501"