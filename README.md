# Interview Intelligence Platform

An AI-powered interview preparation platform that generates personalized mock interviews based on a candidate's resume, job description, and previous interview history.

The goal of the project is to make interview preparation more targeted and focused.

## Overview

The platform takes a candidate's resume and the job they are preparing for, extracts relevant information, and uses it to generate a customized interview.

It uses a retrieval-augmented generation (RAG) pipeline to provide the language model with relevant candidate and job-specific context before generating questions and feedback.

The platform also keeps track of previous interview sessions so that future interviews can be adapted based on the candidate's history.

## Features

- Resume upload and parsing
- Job description-based interview generation
- Personalized technical and behavioral questions
- Resume-aware question generation
- Retrieval-augmented generation using vector search
- Interview session history
- AI-generated feedback on responses
- Authentication and user management
- Persistent storage of interview and candidate data

## Tech Stack
- React
- TypeScript
- Tailwind CSS
- Vite
- FastAPI
- Python
- PostgreSQL
- pgvector
- Redis
- LangChain
- Gemini API
- Vector embeddings
- Retrieval-Augmented Generation (RAG)
- Docker
