# Library
1. pip install flask requests python-dotenv beautifulsoup4 pythainlp sqlalchemy pyodbc schedule

# Run Project
1. python run.py
2. ngrok config add-authtoken #####
3. ./ngrok http 5000

# Run Model
1. python -m model.export_to_csv
2. python -m model.train_pipeline

# Install Database
1. docker pull mcr.microsoft.com/mssql/server:2022-latest
2. docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Inetms@2026" -p 1433:1433 --name sql_server_dev -d mcr.microsoft.com/mssql/server:2022-latest
3. docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Inetms@2026" -p 1434:1433 --name sql_server_prd -d mcr.microsoft.com/mssql/server:2022-latest


# Install Ollama
1. docker run -d --name ollama --restart unless-stopped -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
2. docker exec -it ollama ollama pull qwen2.5vl:3b
3. docker exec -it ollama ollama run qwen2.5vl:3b

# Edit size docker
1. C:\Users\eae_0\.wslconfig
2. Run "wsl --shutdown" on PowerSheel