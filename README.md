# Renewable Energy Projects Analysis Pipeline

A comprehensive system for scraping, analyzing, and visualizing renewable energy projects in Bangladesh, with AI-powered opposition analysis and an interactive web dashboard.

## 🌱 Overview

This project provides a complete pipeline for:
1. **Web Scraping**: Extracting renewable energy project data from SREDA website
2. **AI Analysis**: Using Gemini AI to analyze projects for opposition evidence
3. **Data Visualization**: Interactive Streamlit dashboard for exploring projects
4. **Export Capabilities**: KML files for GIS mapping and CSV exports

## 🚀 Quick Start

### Option 1: Streamlit Cloud (Recommended for Dashboard)
1. Fork this repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Connect your GitHub account and select this repository
4. Deploy!

### Option 2: Local Installation
```bash
git clone https://github.com/yourusername/renewable-energy-dashboard.git
cd renewable-energy-dashboard
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 📁 Project Structure

```
renewable-energy-dashboard/
├── streamlit_app.py              # Main dashboard application
├── scraper.py                    # SREDA website scraper
├── opposition_analyzer.py        # AI-powered opposition analysis
├── requirements.txt              # Python dependencies
├── renewable_energy_projects.csv # Main project dataset (76 projects)
├── summary/                      # Opposition analysis results
│   ├── 125.json
│   ├── 127.json
│   └── ...
├── content/                      # Scraped content for analysis
├── search/                       # Search query results
├── result/                       # Search result metadata
├── raw_html_output/              # Raw HTML from scraping
└── sreda_renewable_energy_projects.kml # GIS mapping file
```

## 🔧 Core Components

### 1. Web Scraping (`scraper.py`)
**Purpose**: Extract renewable energy project data from SREDA website

**Features**:
- Scrapes project listings and detailed information
- Handles pagination and dynamic content
- Extracts 76 renewable energy projects
- Saves data in CSV format with geographic coordinates
- Generates KML files for GIS mapping

**Usage**:
```bash
python scraper.py
```

**Output**:
- `renewable_energy_projects.csv` - Main dataset
- `sreda_renewable_energy_projects.kml` - GIS mapping file
- `raw_html_output/` - Raw HTML files for debugging

### 2. AI Opposition Analysis (`opposition_analyzer.py`)
**Purpose**: Analyze projects for evidence of opposition or conflict using AI

**Features**:
- **AI-Powered Search**: Uses Gemini API to generate optimized search queries
- **Multi-language Support**: Searches in both English and Bangla
- **Comprehensive Web Search**: Uses Brightdata SERP API for Google searches
- **Content Extraction**: Extracts machine-readable content from web pages
- **Opposition Detection**: AI analysis of content for opposition evidence
- **Structured Output**: Saves all results in JSON format

**Pipeline Steps**:
1. Generate search queries (English + Bangla)
2. Execute web searches using Brightdata API
3. Extract content from found URLs
4. Analyze content for opposition evidence
5. Save structured results

**Usage**:
```python
from opposition_analyzer import OppositionAnalyzer

analyzer = OppositionAnalyzer()
result = analyzer.analyze_project(project_data)
```

**API Keys Required**:
- `GEMINI_API_KEY`: Get from Google AI Studio
- `BRIGHTDATA_SERP_API_KEY`: Get from Brightdata dashboard

**Output Structure**:
- `search/` - Generated search queries
- `result/` - Search results with URLs
- `content/` - Extracted content from URLs
- `summary/` - Final opposition analysis

### 3. Interactive Dashboard (`streamlit_app.py`)
**Purpose**: Web-based interface for exploring and analyzing project data

**Features**:
- **Project Explorer**: Browse and select projects with detailed information
- **Advanced Filtering**: Search by name, location, agency, capacity, status
- **Analytics Dashboard**: Charts showing technology distribution, status analysis
- **Opposition Analysis**: Visual indicators and detailed summaries
- **Data Export**: Download filtered data as CSV
- **Responsive Design**: Works on desktop and mobile

**Key Capabilities**:
- Search and filter 76 renewable energy projects
- View detailed project information including capacity, location, agency
- See opposition analysis with confidence scores and source links
- Export filtered datasets
- Interactive charts and visualizations

## 📊 Data Overview

### Project Dataset
- **76 renewable energy projects** from Bangladesh
- **Project details**: Name, capacity, location, technology, agency, status
- **Geographic data**: Latitude and longitude coordinates
- **Technical specs**: DC/AC capacity, grid status, completion dates

### Opposition Analysis
- **11 projects** with detailed opposition analysis
- **7 projects** with confirmed opposition evidence
- **Comprehensive summaries** with confidence scores and source links
- **Multi-language search** in English and Bangla

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Git
- API keys for Gemini and Brightdata (for opposition analysis)

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/renewable-energy-dashboard.git
cd renewable-energy-dashboard

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (for opposition analysis)
cp .env.template .env
# Edit .env with your API keys
```

### Running the Dashboard
```bash
streamlit run streamlit_app.py
```
Access at: http://localhost:8501

### Running the Scraper
```bash
python scraper.py
```

### Running Opposition Analysis
```python
from opposition_analyzer import OppositionAnalyzer
analyzer = OppositionAnalyzer()
# Analyze specific project
result = analyzer.analyze_project(project_data)
```

## 📈 Usage Examples

### Finding Projects with Opposition
1. Open the Streamlit dashboard
2. Look for ⚠️ indicators in the project list
3. Click on projects to see detailed opposition analysis
4. View confidence scores and source links

### Filtering by Capacity
1. Use the capacity range slider in the sidebar
2. Set minimum and maximum capacity values
3. View filtered results across all tabs

### Exporting Data
1. Apply your desired filters
2. Go to the "Raw Data" tab
3. Click "Download filtered data as CSV"

### GIS Mapping
1. Use the generated KML file in GIS software
2. Import `sreda_renewable_energy_projects.kml`
3. Visualize projects on maps

## 🔍 Search Query Strategy

The opposition analysis uses targeted search queries:

**English queries**: Project name + location + "land acquisition solar protest farmer"

**Bangla queries**: Project name + location + "কৃষক জমি দখল আন্দোলন প্রতিবাদ অভিযোগ"

This maximizes finding content about:
- Land acquisition issues
- Farmer protests
- Solar project opposition
- Community conflicts
- Environmental concerns

## 📋 Dependencies

### Core Dependencies
- `streamlit>=1.28.0` - Web dashboard
- `pandas>=2.0.0` - Data manipulation
- `plotly>=6.0.0` - Interactive visualizations
- `requests>=2.25.0` - HTTP requests
- `beautifulsoup4>=4.9.0` - HTML parsing
- `lxml>=4.6.0` - XML/HTML processing

### AI Analysis Dependencies
- `google-generativeai>=0.3.0` - Gemini AI API
- `unstructured>=0.10.0` - Content extraction
- `python-dotenv>=0.19.0` - Environment variables

### Optional Dependencies
- `watchdog>=2.1.0` - File monitoring
- `jupyter>=1.0.0` - Notebook development

## 🚀 Deployment

### Streamlit Cloud
1. Fork this repository
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Connect GitHub and select repository
4. Deploy with default settings

### Local Server
```bash
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0"]
```

## 🔧 Development

### Running Tests
```bash
python test_streamlit_app.py
```

### Adding New Data
1. Update `renewable_energy_projects.csv`
2. Add opposition analysis files to `summary/`
3. Test the application locally
4. Commit and push changes

### Customization
- **Styling**: Modify CSS in `streamlit_app.py`
- **Data Sources**: Update scraping functions
- **Analysis**: Modify opposition analysis logic
- **Visualizations**: Customize charts and graphs

## 📄 API Documentation

### OppositionAnalyzer Class
```python
class OppositionAnalyzer:
    def __init__(self, gemini_api_key, brightdata_api_key)
    def analyze_project(self, project_data) -> dict
    def generate_search_queries(self, project_data) -> dict
    def search_web(self, query, language) -> dict
    def extract_content(self, url) -> dict
    def analyze_opposition(self, content) -> dict
```

### Data Models
- **SearchQueries**: English and Bangla search queries
- **SearchResults**: URLs and metadata from searches
- **ContentExtraction**: Extracted text content
- **OppositionAnalysis**: Final analysis with confidence scores

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions or issues:
1. Check the [Issues](https://github.com/yourusername/renewable-energy-dashboard/issues) page
2. Create a new issue with detailed description
3. Include error messages and steps to reproduce

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Data sourced from SREDA (Sustainable and Renewable Energy Development Authority)
- AI analysis powered by Google Gemini
- Web search powered by Brightdata
- Built with Streamlit, Pandas, and Python

---

**Note**: This project is designed for research and analysis purposes. Ensure compliance with website terms of service and API usage policies when scraping and analyzing data.