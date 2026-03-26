# Library
1. pip install flask requests python-dotenv beautifulsoup4 pythainlp sqlalchemy pyodbc

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
