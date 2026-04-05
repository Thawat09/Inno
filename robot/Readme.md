# Library
1. pip install flask requests python-dotenv beautifulsoup4 pythainlp sqlalchemy psycopg2-binary schedule

# Run Project
1. python run.py
2. ngrok config add-authtoken #####
3. ./ngrok http 5000

# Run Model
1. python -m model.export_to_csv
2. python -m model.train_pipeline

# Install Database
1. docker pull postgres:16.2
2. docker run -d --name postgres_prd -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=Inetms@2026 -e POSTGRES_DB=inno -p 5432:5432 -v postgres_data:/var/lib/postgresql/data postgres:16

# Install Ollama
1. docker run -d --name ollama --restart unless-stopped -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
2. docker exec -it ollama ollama pull qwen2.5vl:3b
3. docker exec -it ollama ollama run qwen2.5vl:3b

# Edit size docker
1. C:\Users\eae_0\.wslconfig
2. Run "wsl --shutdown" on PowerSheel