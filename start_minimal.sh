#!/bin/bash

echo "🚀 Starting Minimal Thinking Graph"
echo "=================================="
echo ""
echo "📦 Installing minimal dependencies..."
pip3 install -q -r minimal_requirements.txt

echo "🔍 Checking Neo4j connection..."
if python3 -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()
try:
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password'))
    )
    with driver.session() as session:
        session.run('RETURN 1')
    print('✅ Neo4j connected')
    driver.close()
except Exception as e:
    print('❌ Neo4j connection failed:', e)
    exit(1)
"; then
    echo ""
    echo "🌟 Starting minimal application..."
    echo "📱 Open http://localhost:8080 in your browser"
    echo "🛑 Press Ctrl+C to stop"
    echo ""
    python3 minimal_app.py
else
    echo ""
    echo "Please ensure Neo4j is running and configured in .env file"
    exit 1
fi