*AI-Powered Healthcare CRM

This is a full-stack Customer Relationship Management (CRM) system I built specifically for the healthcare and pharmaceutical industry. The goal of this project is to eliminate tedious manual data entry. Instead of clicking through complex forms, medical representatives can log interactions, update records, search past meetings, and draft communications entirely through a natural language chatbot.

*Core Features

At the heart of this application is a LangGraph multi-agent workflow. When a user types a message, the AI acts as a router, intelligently passing the request to one of five specialized tools:

Form Filling: The AI reads unstructured conversational notes, extracts the important details (like dates, attendees, and discussion topics), perfectly maps them to the CRM form, and saves the data to PostgreSQL.

Form Editing: Users can dynamically update existing records just by chatting. For example, typing "Change the meeting date to tomorrow" will update that specific field in the database without overwriting the rest of the form.

Contextual Querying: The chatbot is connected to the database history. Users can ask questions about past meetings, and the AI will retrieve the recent context to provide accurate, conversational answers.

Email Drafting: Based on the notes provided about a recent interaction, the AI can automatically draft a polite, professional follow-up email tailored to the healthcare professional.

Compliance Checker: This acts as a strict safety guardrail. Before any data is saved to the database, this tool screens the input for bribery, illegal incentives, or off-label drug promotion. If a compliance issue is detected, the entry is blocked.

*Tech Stack

Frontend: React.js, Tailwind CSS

Backend: FastAPI (Python), SQLAlchemy

Database: PostgreSQL

AI & Orchestration: LangGraph, LangChain, Groq API (Llama-3.1-8b)

How to Run Locally

Prerequisites

Node.js and npm

Python 3.10+

PostgreSQL running locally

A Groq API Key

*1. Database Setup

Ensure PostgreSQL is running on your machine. The backend connects using the DATABASE_URL environment variable. By default, it expects:
postgresql+psycopg://postgres:postgres@localhost:5432/hcp_crm

*2. Backend Setup

Navigate to the backend directory, set up your virtual environment, and install the required packages:

cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt


Create a .env file in the backend folder and add your API key:

GROQ_API_KEY=your_api_key_here


Start the backend server:

uvicorn main:app --reload


*3. Frontend Setup

Open a new terminal, navigate to the frontend directory, install the dependencies, and start the development server:

cd frontend
npm install
npm start


The React application will be available at http://localhost:3000.
