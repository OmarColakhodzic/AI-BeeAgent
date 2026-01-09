# BeeAgent - Intelligent Beekeeping Assistant

## Overview
BeeAgent is an autonomous software agent that helps beekeepers make data-driven decisions by analyzing hive sensor data (temperature, humidity, frame count, colony strength, varroa levels). Using machine learning, it provides actionable recommendations through an asynchronous, queue-based processing system.

## How It Works

### Core Architecture
The system follows Clean Architecture with four distinct layers:

1. **Domain Layer** - Core business entities (Observation, Prediction, ActionType)
2. **Application Layer** - Business logic and agent runners implementing the Sense→Think→Act cycle
3. **Infrastructure Layer** - Technical implementations (database, ML model)
4. **Web Layer** - Thin API layer (FastAPI endpoints)

### The Agent Cycle
BeeAgent operates autonomously in the background using a continuous loop:

1. **SENSE** - Monitors the queue for new observations from beekeepers
2. **THINK** - Processes data through ML models and business rules
3. **ACT** - Stores predictions and updates observation status

This cycle runs independently of API requests, ensuring real-time processing without blocking user interactions.

### Learning Capability
The system improves over time through user feedback. When beekeepers reject a recommendation and provide the correct action, the agent uses this feedback to retrain and improve future predictions.

## Key Features

- **Autonomous Operation**: Runs continuously in background threads
- **Asynchronous Processing**: Requests are queued and processed independently
- **Machine Learning Integration**: Uses scikit-learn for prediction models
- **Feedback Learning**: Continuously improves from user corrections
- **RESTful API**: Simple endpoints for integration
- **Web Dashboard**: React-based interface for monitoring

## Installation & Setup

### Backend Setup
1. cd backend
2. python -m venv venv
3. venv\Scripts\activate
4. pip install -r requirements.txt
5. python main.py

### Frontend Setup
1. cd frontend
2. npm install
3. npm start

## Why It's an Agent (Not Just an API)

Unlike traditional ML APIs that process requests synchronously, BeeAgent:
- Operates continuously without user initiation
- Maintains state through a processing queue
- Implements a complete cognitive cycle (Sense→Think→Act)
- Learns autonomously from interactions
- Runs independently in background threads

## Practical Benefits for Beekeepers

1. **Immediate Response**: Requests are queued and processed rapidly
2. **Continuous Monitoring**: Agent works even when users aren't actively using the system
3. **Improved Accuracy**: Learning from feedback creates better recommendations over time
4. **Non-blocking Interface**: Users can submit data and check back later for results
5. **Actionable Insights**: Clear recommendations like "check varroa," "feed colony," or "no action needed"

The system demonstrates how autonomous agents can provide intelligent assistance in agricultural contexts while maintaining clean, maintainable architecture suitable for production deployment.
