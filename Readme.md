# Library
1. pip install flask requests python-dotenv beautifulsoup4 pythainlp sqlalchemy pyodbc google-genai

# Run Project
1. python run.py
2. ngrok config add-authtoken #####
3. ./ngrok http 5000

# Run Model
1. python -m model.export_to_csv
2. python -m model.train_model

# Install Database
1. docker pull mcr.microsoft.com/mssql/server:2022-latest
2. docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Inetms@2026" -p 1433:1433 --name sql_server_dev -d mcr.microsoft.com/mssql/server:2022-latest

# Install Llama
1. docker run -d --name ollama -v ollama:/root/.ollama -p 11434:11434 ollama/ollama
2. docker exec -it ollama ollama pull llama3.2
3. docker exec -it ollama ollama run llama3.2

<!-- curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "สรุป AWS IAM เป็นภาษาไทยแบบเข้าใจง่าย"
}' -->