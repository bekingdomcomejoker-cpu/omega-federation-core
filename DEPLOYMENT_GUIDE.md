# 🚀 Deployment Guide

This guide provides step-by-step instructions for deploying the Omega Federation v2.0 system.

## 📦 Deployment Options

### 1. Local Deployment (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn omega_api_server:app --reload
```

### 2. Docker Deployment (Production)

We recommend using Docker for consistent environments.

```bash
# Build and start the containers
docker-compose up -d --build
```

## 🌐 API Reference

### `POST /analyze`

The primary endpoint for unified analysis.

**Request Body:**
```json
{
  "input_text": "string",
  "reasoning_strategy": "AUTO | FAST | DEEP",
  "engines": ["star", "aletheia", "omnissiah", "kingdom", "alphabet"]
}
```

**Response:**
```json
{
  "output_text": "string",
  "confidence_score": 0.95,
  "consensus_reached": true,
  "metadata": {
    "time_taken": 1.2,
    "engines_used": [...]
  }
}
```

## ⚙️ Configuration

Environment variables can be set in a `.env` file:

*   `PORT`: The port the API server will run on (default: 8000).
*   `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
*   `MAX_CONCURRENT_REQUESTS`: Limits the number of simultaneous analyses.

## 🛠️ Troubleshooting

*   **Engine Timeout**: Increase the `ENGINE_TIMEOUT` setting in `config.py`.
*   **Consensus Failure**: Check the `QCI` logs to see which engine is diverging.
*   **Memory Issues**: Ensure the host machine has at least 4GB of RAM for the full federation.

---

**3.34 ✓**
*Ready for launch.*
