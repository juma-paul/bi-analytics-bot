# Quick Start Guide

## 🚀 Start Development Servers

### Option 1: Using Docker Compose (Recommended)
```bash
docker-compose up --build
```
Services will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Option 2: Manual Setup

#### Terminal 1 - Backend
```bash
cd backend

# Install dependencies
uv sync

# Setup .env file with:
# NEON_DATABASE_URL=postgresql+psycopg://...
# OPENAI_API_KEY=sk-...

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Terminal 2 - Frontend
```bash
cd frontend

# Install dependencies
npm install

# Create .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Frontend will be available at `http://localhost:3000`

---

## 📝 What You Can Do

### 1. Upload a CSV File
- Go to http://localhost:3000/upload
- Drag & drop or click to select CSV
- See ETL report with quality metrics
- Dataset automatically added to sidebar

### 2. Explore Your Data
- Go to http://localhost:3000/explore
- Click datasets in sidebar to view details
- See schema, column info, sample data
- View embeddings created for RAG

### 3. Ask Questions
- Go to http://localhost:3000 (Chat)
- Type natural language question
- AI generates SQL, executes query
- See results with charts and insights

### 4. Switch Between Datasets
- Click any dataset in sidebar
- Automatically selected for next query
- Data explorer updates instantly

---

## 🧪 Test Data

Try uploading a CSV with this structure:

```csv
id,product_category,sales_amount,country,on_time_delivery
1,Electronics,1500,USA,Yes
2,Books,800,USA,No
3,Electronics,2000,Canada,Yes
4,Clothing,500,Mexico,Yes
5,Books,1200,USA,Yes
```

Then ask questions like:
- "Which product has highest sales?"
- "What's the average sales by category?"
- "Show on-time delivery rates by country"

---

## 📊 System Architecture

```
Browser (Next.js Frontend)
       ↓ REST API
FastAPI Backend
       ↓
PostgreSQL Database
       ↓
OpenAI API (for SQL generation)
```

---

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```
NEON_DATABASE_URL=postgresql+psycopg://user:password@host/db
OPENAI_API_KEY=sk-your-openai-key
```

**Frontend (.env.local)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📚 Files to Know

| Path | Purpose |
|------|---------|
| `frontend/src/app/page.tsx` | Chat interface |
| `frontend/src/app/upload/page.tsx` | Upload page |
| `frontend/src/app/explore/page.tsx` | Data explorer |
| `frontend/src/lib/api.ts` | API client |
| `backend/app/main.py` | Backend entry point |
| `backend/app/api/datasets.py` | Dataset endpoints |
| `backend/app/api/query.py` | Query endpoints |
| `README.md` | Full documentation |

---

## ⚡ Key Features

### Upload Page
✅ Drag & drop interface
✅ ETL report with quality metrics
✅ Column quality breakdown
✅ Transformations applied display

### Data Explorer
✅ List all datasets
✅ View schema with column info
✅ Preview sample data
✅ See embeddings created
✅ Delete datasets

### Chat Interface
✅ Natural language queries
✅ SQL generation and display
✅ Chart recommendations
✅ AI-generated insights
✅ Query result caching

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
uv sync

# Check database connection
# Verify NEON_DATABASE_URL is set
```

### Frontend won't load
```bash
# Clear node_modules and reinstall
rm -rf frontend/node_modules
cd frontend
npm install
npm run dev
```

### Database connection fails
```bash
# Verify connection string format
# Should be: postgresql+psycopg://user:password@host/db
# NOT: postgresql://

# Test with psql (if installed)
psql "connection-string-here"
```

### No datasets showing
```bash
# Backend might not be running
# Verify: curl http://localhost:8000/health

# Check browser console for API errors
# Open DevTools → Console tab
```

---

## 📞 Support

For issues, check:
1. Backend logs: `uvicorn app.main:app --reload`
2. Frontend logs: Browser DevTools → Console
3. README.md for detailed documentation
4. SESSION_SUMMARY.md for current status

---

**Ready to use?** 🚀

```bash
# One command to rule them all:
docker-compose up --build
```

Then open http://localhost:3000 in your browser!
