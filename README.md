# 🤖 Intelligent Agentic Web Scraper

An intelligent web scraping system built with LangGraph and FastAPI that autonomously crawls websites, extracts content, and generates AI-powered summaries. Features state management, conditional routing, automatic error handling with retry logic, and async job processing.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.6+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

<img width="445" height="527" alt="image" src="https://github.com/user-attachments/assets/946e5b2b-3f4e-4864-96cb-73582164a39e" />

## 🌟 Features

- **🔄 Agentic Workflow**: Built with LangGraph for intelligent state management and conditional routing
- **⚡ Async Processing**: Background job execution with real-time status tracking
- **🔁 Smart Error Handling**: Automatic retry logic (max 3 retries) with graceful degradation
- **🎯 Intelligent Filtering**: Advanced URL validation excluding login pages, cart pages, and irrelevant content
- **📦 Batch Processing**: Configurable batch limits to respect API rate limits
- **🤖 AI-Powered Summaries**: Google Gemini integration for structured content summarization
- **🐳 Docker Ready**: Fully containerized for easy deployment
- **📊 RESTful API**: Well-documented endpoints with automatic OpenAPI/Swagger docs
- **☁️ Cloud Deployed**: Production deployment on Render with CI/CD

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │  ← RESTful API with async endpoints
└──────┬──────┘
       │
┌──────▼───────────────────────────────────────┐
│           LangGraph Agent                    │
│  ┌──────────────────────────────────────┐   │
│  │  Initialize → Crawl → Scrape         │   │
│  │       ↓         ↓         ↓          │   │
│  │  Format → Save → Error Handler       │   │
│  └──────────────────────────────────────┘   │
└──────┬───────────────────────────────────────┘
       │
┌──────▼──────┐    ┌──────────┐    ┌─────────┐
│  Firecrawl  │    │  Gemini  │    │  JSON   │
│     API     │    │   LLM    │    │ Storage │
└─────────────┘    └──────────┘    └─────────┘
```

### Workflow Nodes

1. **Initialize**: Sets up initial state with URL and empty data structures
2. **Crawl**: Uses Firecrawl to discover all links on the target page
3. **Scrape**: Batch scrapes discovered URLs to extract markdown content
4. **Format**: Uses Gemini to generate structured summaries (title + description)
5. **Save**: Persists formatted data to JSON file
6. **Error Handler**: Manages retries and error recovery

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker (optional)
- API Keys:
  - [Firecrawl API Key](https://firecrawl.dev)
  - [Google Gemini API Key](https://ai.google.dev)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/web-scraper-agent.git
cd web-scraper-agent
```

2. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
FIRECRAWL_API_KEY=your_firecrawl_api_key
GOOGLE_API_KEY=your_google_api_key
URL_LIMIT=50          # Max URLs to scrape per job
BATCH_LIMIT=10        # URLs per batch
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the server**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Using Docker

```bash
# Build the image
docker build -t web-scraper .

# Run the container
docker run -p 8000:8000 --env-file .env web-scraper
```

## 📖 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### 1. Create Scraping Job (Async)
```bash
POST /scrape
Content-Type: application/json

{
  "url": "https://example.com"
}

Response (202):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scraping job created successfully",
  "created_at": "2025-11-01T10:30:00"
}
```

#### 2. Check Job Status
```bash
GET /jobs/{job_id}

Response (200):
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "url": "https://example.com",
  "created_at": "2025-11-01T10:30:00",
  "completed_at": "2025-11-01T10:32:15",
  "result": { ... },
  "error": null
}
```

#### 3. Get Job Results
```bash
GET /jobs/{job_id}/result

Response (200):
{
  "source_url": "https://example.com",
  "data": [
    {
      "url": "https://example.com/page1",
      "response": {
        "title": "Page Title",
        "description": "AI-generated summary of the page content..."
      }
    }
  ]
}
```

#### 4. Scrape Synchronously
```bash
POST /scrape/sync
Content-Type: application/json

{
  "url": "https://example.com"
}

# Waits for completion and returns result directly
```

#### 5. List All Jobs
```bash
GET /jobs?status=completed&limit=10
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIRECRAWL_API_KEY` | Firecrawl API key | Required |
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `URL_LIMIT` | Max URLs to scrape per job | 50 |
| `BATCH_LIMIT` | URLs per batch | 10 |

### URL Filtering

The system automatically filters out:
- ❌ Login/logout pages
- ❌ Account/profile pages
- ❌ Cart/checkout pages
- ❌ Payment pages
- ❌ Admin panels
- ❌ Privacy/terms pages
- ❌ File downloads (PDFs, images, archives)
- ❌ Anchor links
- ❌ JavaScript/mailto links
- ❌ Cross-domain URLs

Edit `excluded_patterns` in `agent/utils/helpers.py` to customize.

## 📊 Example Output

```json
{
  "source_url": "https://quotes.toscrape.com/",
  "data": [
    {
      "url": "https://quotes.toscrape.com/tag/inspirational/",
      "response": {
        "title": "Inspirational Quotes Collection",
        "description": "This content showcases a selection of inspirational quotes from renowned authors like Albert Einstein, Marilyn Monroe, and Thomas A. Edison, each accompanied by their respective tags."
      }
    },
    {
      "url": "https://quotes.toscrape.com/tag/life/",
      "response": {
        "title": "Quotes Tagged 'Life'",
        "description": "This page features famous sayings by Albert Einstein and André Gide, offering perspectives on living authentically and embracing life's challenges."
      }
    }
  ]
}
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=agent --cov-report=html

# Run specific test file
pytest tests/test_helpers.py -v
```

## 🚢 Deployment

### Deploy to Render

1. **Connect GitHub repository** to Render
2. **Create new Web Service**
3. **Configure**:
   - Environment: Docker
   - Branch: main
   - Add environment variables (API keys)
4. **Deploy** - Render auto-detects Dockerfile

### Deploy to AWS ECS (Production)

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t web-scraper .
docker tag web-scraper:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/web-scraper:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/web-scraper:latest

# Deploy with ECS
aws ecs update-service --cluster my-cluster --service web-scraper --force-new-deployment
```

## 🎯 Use Cases

- **Content Aggregation**: Automatically aggregate blog posts, articles, or news
- **Competitive Intelligence**: Monitor competitor websites for changes
- **Research**: Gather and summarize academic papers or documentation
- **Price Monitoring**: Track product prices across e-commerce sites
- **Job Aggregation**: Collect job postings from multiple career sites
- **Real Estate**: Aggregate property listings with summaries

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI 0.104+
- **Agent Framework**: LangGraph 0.2.6+
- **LLM**: Google Gemini 2.5 Flash via LangChain
- **Web Scraping**: Firecrawl API
- **Language**: Python 3.12
- **Containerization**: Docker
- **Deployment**: Render Cloud Platform

## 📈 Performance

- **Average job completion**: 2-5 minutes (depends on URL count)
- **Concurrent jobs**: Supports multiple via background tasks
- **Rate limiting**: Batch processing respects API limits
- **Error recovery**: Automatic retry up to 3 attempts

## ⚠️ Limitations & Production Considerations

### Current Limitations
- ✅ In-memory job storage (lost on restart)
- ✅ Single server processing
- ✅ No authentication/authorization
- ✅ No rate limiting per user
- ✅ Basic error logging

### Production Recommendations

1. **Replace in-memory storage** with Redis/PostgreSQL
2. **Add authentication** (API keys, OAuth)
3. **Implement rate limiting** (per user/API key)
4. **Use Celery** for distributed task processing
5. **Add monitoring** (Prometheus, Grafana)
6. **Implement caching** (don't re-scrape recent URLs)
7. **Add proper logging** (structured logs, ELK stack)
8. **Cost tracking** (monitor Firecrawl/LLM API usage)
9. **Add webhooks** (notify on job completion)
10. **Security hardening** (SSRF protection, input validation)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [Firecrawl](https://firecrawl.dev) for robust web scraping
- [FastAPI](https://fastapi.tiangolo.com) for the excellent web framework
- [Google Gemini](https://ai.google.dev) for AI-powered summaries

## 📧 Contact

Your Name - [@yourtwitter](https://twitter.com/yourtwitter) - email@example.com

Project Link: [https://github.com/yourusername/web-scraper-agent](https://github.com/yourusername/web-scraper-agent)

---

**⭐ If you find this project useful, please consider giving it a star!**
