# AI BI Data Analyst

> **Natural language querying for BI analytics with AI-powered SQL generation, enterprise-grade ETL, and dynamic visualizations**

Democratize data access by allowing anyone to query their data using plain English instead of SQL. Upload CSV files, get automated data quality reports, and ask natural language questions to explore your data.

## 🎯 Value Proposition

**The Problem:** Data analytics requires SQL knowledge, limiting insights to technical teams.

**The Solution:** AI-powered natural language interface that:
- **Accepts any CSV file** and runs comprehensive data quality checks
- **Understands your data** through intelligent ETL pipeline (validation → cleaning → transformation → profiling)
- **Generates accurate SQL** using hybrid Text-to-SQL + RAG approach
- **Creates visualizations automatically** with AI-recommended chart types
- **Provides insights** through AI analysis of query results

**Who Benefits:**
- Business analysts without SQL knowledge
- Data teams wanting faster ad-hoc analysis
- Organizations standardizing analytics access
- Anyone exploring datasets without writing code

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14 + React 18)                              │
│  • Chat Interface - Ask questions naturally                     │
│  • Data Explorer - Browse datasets and schema                   │
│  • Upload Page - CSV with ETL progress                          │
│  • Visualizations - Dynamic charts with Recharts               │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST API (axios)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + LangChain)                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ETL Pipeline (Production-Grade)                         │  │
│  │  • File Validation (format, encoding, size)              │  │
│  │  • Data Type Detection (20+ format support)              │  │
│  │  • Smart Cleaning (duplicates, nulls, outliers)          │  │
│  │  • Data Transformation (type conversion, dates)          │  │
│  │  • Profiling & Quality Scoring (0-100)                   │  │
│  │  • PostgreSQL Loading (COPY, indexing, validation)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                        │
│  ┌────────────────────┴────────────────────────────────────┐   │
│  │                                                         │   │
│  ▼                          ▼                              ▼   │
│ RAG System              LLM Query Engine            Chart Advisor│
│ • pgvector              • Text-to-SQL             • Chart Selection
│ • Embeddings            • LangChain                • Config Gen
│ • Semantic Search       • OpenAI GPT-4             • Insight Gen
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Database (PostgreSQL + pgvector on Neon)                       │
│                                                                  │
│  • datasets - Dataset metadata                                  │
│  • dataset_columns - Column info + quality metrics              │
│  • dataset_embeddings - Vector embeddings for RAG               │
│  • user_data_* - Dynamic tables for uploaded datasets            │
│  • query_cache - Query result caching                           │
│  • etl_logs - Complete ETL execution audit trail               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. **Production-Grade ETL Pipeline**
Upload any CSV file and get a comprehensive quality report:
- **7-Stage Processing**: Validation → Detection → Cleaning → Transformation → Profiling → Loading → Reporting
- **Smart Type Detection**: Handles 20+ formats (currencies, dates, booleans, encodings)
- **Intelligent Cleaning**:
  - Exact & fuzzy duplicate detection
  - Smart missing value strategies
  - Outlier detection (IQR + Z-score)
  - Automatic data standardization
- **Quality Scoring**: 0-100 score based on completeness, validity, consistency, uniqueness
- **Column Profiling**: Statistics, distributions, quality issues per column

### 2. **Hybrid AI Query Engine**
Ask questions in natural language:
- **Text-to-SQL**: Converts natural language to accurate PostgreSQL queries
- **RAG (Retrieval-Augmented Generation)**: Uses pgvector semantic search to retrieve dataset context for better accuracy
- **Smart Context**: Understands table structure, column meanings, and data patterns
- **SQL Validation**: Automatic validation and error handling with retry logic
- **Query Caching**: Speeds up repeated questions

### 3. **Dynamic Visualizations**
Automatic chart generation:
- **Smart Recommendations**: AI suggests best chart type based on data
- **Chart Types**: Bar, Line, Pie, Table
- **Interactive Display**: Responsive, mobile-friendly charts
- **Data Export**: Download results

### 4. **Data Explorer**
Browse and understand your data:
- **Dataset Listing**: See all uploaded datasets with quality scores
- **Schema Viewer**: Column information, data types, quality metrics
- **Data Preview**: Sample rows from each dataset
- **Embeddings Viewer**: See vector embeddings created for RAG
- **Quality Reports**: Detailed ETL metrics and transformations

### 5. **Enterprise Features**
Production-ready system:
- **Multi-Dataset Support**: Switch between datasets instantly
- **User-Friendly Design**: Apple/Linear aesthetic with responsive UI
- **Error Handling**: Comprehensive error messages with suggestions
- **Audit Logging**: Complete ETL and query execution logs
- **Performance**: Query caching, optimized indexes, connection pooling

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL database** (Neon serverless recommended)
- **OpenAI API key** (GPT-4 access)

### Local Development Setup

#### 1. Clone & Setup Backend

```bash
cd backend

# Install Python dependencies with uv
uv sync

# Create .env file with your credentials
cat > .env << EOF
NEON_DATABASE_URL=postgresql+psycopg://user:password@host/dbname
OPENAI_API_KEY=sk-your-key-here
EOF

# Run migrations (if applicable)
python -m alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

#### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

#### 3. Using Docker (Optional)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Services will start:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - PostgreSQL: localhost:5432
```

---

## 📊 Example Workflow

### 1. Upload Data
```
Upload CSV file → ETL pipeline runs → Quality report shown
Output:
  - Data quality score: 92.5%
  - Rows cleaned: 488 duplicates removed
  - Columns profiled: 7 columns analyzed
```

### 2. Ask Questions
```
"Which product categories have the highest sales?"
↓
AI generates SQL with schema context
↓
Query executes and caches result
↓
Chart recommended: Bar chart by category
↓
Insights generated automatically
```

### 3. Explore Data
```
Data Explorer → Dataset Schema → Column Statistics
Show:
  - Data types and nullable status
  - Unique value counts
  - Quality issues detected
  - Sample values for each column
```

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000
```

### Dataset Endpoints

#### Upload Dataset
```
POST /api/datasets/upload

Content-Type: multipart/form-data
- file: CSV file
- dataset_name: Optional name (defaults to filename)

Response:
{
  "success": true,
  "dataset_id": "uuid",
  "dataset": {...},
  "etl_report": {
    "summary": {
      "original_rows": 19722,
      "final_rows": 19234,
      "rows_removed": 488,
      "data_quality_score": 92.5
    },
    "cleaning_report": {...},
    "transformations": [...]
  }
}
```

#### List Datasets
```
GET /api/datasets

Response:
{
  "datasets": [
    {
      "id": "uuid",
      "name": "Sales Data",
      "table_name": "user_data_sales_data",
      "row_count": 19234,
      "column_count": 7,
      "data_quality_score": 92.5,
      "etl_status": "completed"
    }
  ],
  "total": 1
}
```

#### Get Dataset Schema
```
GET /api/datasets/{dataset_id}/schema

Response:
{
  "dataset_id": "uuid",
  "columns": [
    {
      "column_name": "product_category",
      "data_type": "VARCHAR",
      "nullable": false,
      "unique_count": 45,
      "null_count": 0,
      "sample_values": ["Electronics", "Books", ...]
    }
  ]
}
```

#### Get Data Preview
```
GET /api/datasets/{dataset_id}/preview?limit=10

Response:
{
  "columns": ["id", "product_category", "sales"],
  "rows": [
    {"id": 1, "product_category": "Electronics", "sales": 1500},
    ...
  ]
}
```

#### Get Embeddings
```
GET /api/datasets/{dataset_id}/embeddings

Response:
{
  "dataset_id": "uuid",
  "embeddings": [
    {
      "id": "uuid",
      "content": "Table has columns: product_category (VARCHAR)...",
      "embedding_type": "schema",
      "embedding_metadata": {...},
      "created_at": "2024-01-10T10:30:00Z"
    }
  ]
}
```

#### Delete Dataset
```
DELETE /api/datasets/{dataset_id}

Response:
{
  "success": true,
  "message": "Dataset deleted"
}
```

### Query Endpoints

#### Execute Query
```
POST /api/query

{
  "dataset_id": "uuid",
  "question": "What are the top 5 product categories by sales?"
}

Response:
{
  "query_id": "uuid",
  "question": "What are the top 5 product categories by sales?",
  "generated_sql": "SELECT product_category, SUM(sales)...",
  "sql_explanation": "Groups sales by product category and sorts...",
  "results": {
    "columns": ["product_category", "total_sales"],
    "rows": [
      {"product_category": "Electronics", "total_sales": 250000},
      ...
    ],
    "row_count": 5
  },
  "visualization": {
    "type": "bar",
    "config": {
      "xAxis": "product_category",
      "yAxis": "total_sales"
    }
  },
  "insights": [
    "Electronics has 3x higher sales than other categories",
    "Top 5 categories represent 85% of total revenue"
  ],
  "execution_time_ms": 245,
  "cached": false
}
```

---

## 🏛️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, React 18, TypeScript | Modern UI with App Router |
| **Styling** | Tailwind CSS | Custom design system (Apple/Linear inspired) |
| **Charts** | Recharts | Interactive visualizations |
| **State** | Zustand | Global state management |
| **Backend** | FastAPI, Python 3.11+ | High-performance async API |
| **AI/LLM** | LangChain, OpenAI GPT-4 | SQL generation & insights |
| **Database** | PostgreSQL + pgvector | Structured data + vector embeddings |
| **Embeddings** | OpenAI text-embedding-3-small | 1536-dimensional vectors for RAG |
| **Hosting** | Docker, Docker Compose | Local development & deployment |
| **Cloud DB** | Neon | Serverless PostgreSQL |

---

## 📈 ETL Pipeline Details

### 7-Stage Processing

**Stage 1: File Validation**
- Format check (.csv only)
- File size validation (< 50MB)
- Encoding detection (UTF-8, Latin-1, etc.)
- Structure validation (consistent columns)

**Stage 2: Type Detection**
- Intelligent type inference
- Support for 20+ data formats
- Encoding & delimiter detection
- Missing value recognition

**Stage 3: Data Cleaning**
- Exact duplicate removal
- Fuzzy duplicate detection (95%+ match)
- Smart missing value handling
- Outlier detection & handling

**Stage 4: Data Transformation**
- Column name standardization (snake_case)
- Data type conversion
- Date format parsing (15+ formats)
- Categorical value standardization

**Stage 5: Data Profiling**
- Statistical analysis (mean, median, std, etc.)
- Distribution generation
- Quality scoring algorithm
- Issue identification

**Stage 6: PostgreSQL Loading**
- Dynamic table creation
- Data type mapping
- Index creation on key columns
- Bulk loading with COPY
- Row count verification

**Stage 7: Metadata & Reporting**
- Store all statistics
- Generate quality report
- Create embeddings for RAG
- Log complete audit trail

### Quality Scoring Algorithm

```
Completeness = 100 - (total_nulls / total_cells * 100)
Validity = % of values passing type checks
Consistency = % of standardized values
Uniqueness = 100 - (duplicate_rows / total_rows * 100)

Final Score = (Completeness + Validity + Consistency + Uniqueness) / 4
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build Docker images
docker-compose build

# Run services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Vercel Deployment (Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Backend Deployment (Render/Railway)

```bash
# Backend will be deployed via Docker
# Set environment variables:
# - NEON_DATABASE_URL
# - OPENAI_API_KEY

# Deployment command (automatic via Docker)
docker build -t backend .
docker run -p 8000:8000 backend
```

---

## 🔐 Security

- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Input Validation**: File type, size, and content validation
- **Error Handling**: Generic error messages (no sensitive data exposure)
- **API Authentication**: Ready for JWT/OAuth integration
- **Data Privacy**: No data sent to OpenAI beyond necessary context

---

## 📝 Project Structure

```
.
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                 # Entry point
│   │   ├── database.py             # PostgreSQL + pgvector setup
│   │   ├── config.py               # Environment config
│   │   ├── models/
│   │   │   └── dataset.py          # SQLAlchemy models
│   │   ├── services/
│   │   │   ├── etl_pipeline.py    # Main ETL orchestration
│   │   │   ├── data_validator.py  # File & type validation
│   │   │   ├── data_cleaner.py    # Data cleaning operations
│   │   │   ├── data_transformer.py# Data transformation
│   │   │   ├── data_profiler.py   # Statistical profiling
│   │   │   ├── schema_inference.py# Schema detection
│   │   │   ├── embedding_service.py# Vector embeddings
│   │   │   ├── rag_service.py     # Semantic search
│   │   │   └── sql_generator.py   # Text-to-SQL with LangChain
│   │   ├── api/
│   │   │   ├── datasets.py        # Dataset endpoints
│   │   │   └── query.py           # Query endpoints
│   │   └── core/
│   │       └── exceptions.py      # Custom exceptions
│   ├── .env.example               # Environment template
│   └── pyproject.toml             # Python dependencies
│
├── frontend/                        # Next.js application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout with sidebar
│   │   │   ├── page.tsx           # Chat interface
│   │   │   ├── upload/
│   │   │   │   └── page.tsx       # CSV upload page
│   │   │   ├── explore/
│   │   │   │   └── page.tsx       # Data explorer
│   │   │   └── globals.css        # Global styles
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Sidebar.tsx    # Navigation sidebar
│   │   │   ├── chat/
│   │   │   │   ├── ChatMessage.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── ChatContainer.tsx
│   │   │   ├── query/
│   │   │   │   └── QueryResults.tsx
│   │   │   ├── visualization/
│   │   │   │   ├── ChartRenderer.tsx
│   │   │   │   └── DataTable.tsx
│   │   │   ├── upload/
│   │   │   │   └── ETLReportView.tsx
│   │   │   └── explore/
│   │   │       ├── DatasetCard.tsx
│   │   │       ├── DatasetPreview.tsx
│   │   │       ├── SchemaViewer.tsx
│   │   │       └── EmbeddingsViewer.tsx
│   │   ├── lib/
│   │   │   └── api.ts             # API client
│   │   ├── store/
│   │   │   └── app.ts             # Zustand state store
│   │   └── hooks/
│   ├── tailwind.config.ts         # Design system config
│   ├── package.json               # Node dependencies
│   └── .env.local.example         # Environment template
│
└── docker-compose.yml              # Development orchestration
```

---

## 🧪 Testing

### Manual Testing Checklist

- [ ] **Upload Flow**
  - [ ] Upload valid CSV
  - [ ] Verify ETL report generated
  - [ ] Check data quality score
  - [ ] Verify dataset appears in list

- [ ] **Data Explorer**
  - [ ] View dataset list
  - [ ] Click dataset to select
  - [ ] View schema/columns
  - [ ] Preview data (first 10 rows)
  - [ ] View embeddings

- [ ] **Query Flow**
  - [ ] Ask natural language question
  - [ ] Verify SQL generated
  - [ ] Check results accuracy
  - [ ] View chart visualization
  - [ ] Read AI insights

- [ ] **Error Handling**
  - [ ] Upload non-CSV file
  - [ ] Test with large file (>50MB)
  - [ ] Try invalid question
  - [ ] Delete dataset
  - [ ] Switch between datasets

---

## 🤝 Contributing

This is a portfolio project. For improvements:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/improvement`
3. Commit changes: `git commit -am 'Add improvement'`
4. Push to branch: `git push origin feature/improvement`
5. Submit pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 👨‍💻 About This Project

This project demonstrates:

- **Full-Stack Expertise**: Modern Next.js frontend + FastAPI backend
- **Data Engineering**: Production-grade ETL pipeline with 7 stages
- **AI/LLM Integration**: Hybrid Text-to-SQL + RAG with pgvector
- **Software Architecture**: Scalable, maintainable, production-ready design
- **Database Design**: PostgreSQL schema with proper relationships and indexes
- **API Design**: RESTful endpoints with clear documentation
- **UI/UX**: Modern design inspired by Apple and Linear
- **DevOps**: Docker, Docker Compose, cloud deployment ready

Built to be a strong portfolio project for **BI Engineer**, **Data Engineer**, **ML Engineer**, or **Full-Stack Engineer** roles.

---

**Questions?** Open an issue or check the API documentation above.

**Ready to deploy?** Follow the [Deployment](#-deployment) section.

**Want to contribute?** See [Contributing](#-contributing).
