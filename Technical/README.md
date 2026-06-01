# Wassily - Technical Implementation

**Project:** Input-Output Tables Analysis Tool
**Language:** Python
**Last Updated:** October 10, 2025

---

## Architecture Overview

**Type:** Monolithic analytical tool
**Approach:** Modular functions for I-O analysis, unified interface

Wassily is designed as a comprehensive I-O analysis tool with:
- **Data acquisition module** - Download/load I-O tables from various sources
- **Data processing module** - Standardize and clean I-O tables
- **Analysis module** - Calculate multipliers, linkages, and structural metrics
- **Reporting module** - Generate Excel outputs and LaTeX reports

## Technology Stack

### Core Dependencies
```
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing
openpyxl>=3.1.0        # Excel file handling
xlrd>=2.0.0            # Excel file reading (legacy formats)
```

### Analysis Tools
```
scipy>=1.10.0          # Scientific computing (matrix operations)
networkx>=3.0          # Network analysis (if analyzing I-O as networks)
```

### Visualization (Optional)
```
matplotlib>=3.7.0      # Static plots
seaborn>=0.12.0        # Statistical visualizations
```

### Documentation
```
sphinx>=4.0.0          # Technical documentation (if needed)
```

### Development
```
pytest>=7.0.0          # Testing framework
black>=22.0.0          # Code formatting
flake8>=4.0.0          # Linting
```

## Setup Instructions

```bash
# Navigate to project
cd "D:/Arcanum/Projects/Wassily"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies (once requirements.txt is created)
pip install -r requirements.txt
```

## Data Strategy

### Data Sources

**U.S. Input-Output Tables:**
- Source: Bureau of Economic Analysis (BEA)
- URL: https://www.bea.gov/industry/input-output-accounts-data
- Vintages: [To be cataloged]
- Format: Excel files
- Location: `Technical/data/raw/bea/`

**International Input-Output Tables:**
- OECD I-O tables: https://www.oecd.org/sti/ind/input-outputtables.htm
- WIOD: http://www.wiod.org/
- [Other sources to be determined]
- Location: `Technical/data/raw/international/`

### Data Organization

```
Technical/data/
├── raw/                    # Original I-O tables as published
│   ├── bea/               # BEA U.S. I-O tables (by year)
│   │   ├── 2017/
│   │   ├── 2012/
│   │   └── ...
│   └── international/     # International I-O tables
│       ├── oecd/
│       ├── wiod/
│       └── ...
├── processed/             # Standardized I-O tables
│   ├── us/               # Processed U.S. tables
│   └── international/    # Processed international tables
└── robin_sourced/        # Data from Robin (if applicable)
```

## Code Organization

### src/
[Will document as modules are created]

**Planned Structure:**
- `io_loader.py` - Load I-O tables from various formats
- `io_processor.py` - Standardize and clean I-O tables
- `io_analysis.py` - Core I-O analysis functions
  - Calculate Leontief inverse
  - Compute multipliers
  - Analyze linkages
  - Identify key sectors
- `io_exporter.py` - Export results to Excel/CSV
- `io_reports.py` - Generate LaTeX reports

### scripts/
[Will document as scripts are created]

**Planned Scripts:**
- `download_bea_tables.py` - Automated download of BEA I-O tables
- `process_all_tables.py` - Batch processing of I-O tables
- `generate_reports.py` - Automated report generation

### configs/
[Will document configuration files]

**Planned Configs:**
- `io_sources.yaml` - Data source URLs and metadata
- `analysis_config.yaml` - Analysis parameters and settings

## Input-Output Analysis Methods

### Standard Analyses to Implement:

1. **Leontief Inverse Calculation**
   - Direct requirements matrix (A)
   - Total requirements matrix (L = (I - A)^-1)

2. **Multipliers**
   - Output multipliers
   - Income multipliers
   - Employment multipliers

3. **Linkages**
   - Forward linkages (supply-side)
   - Backward linkages (demand-side)
   - Rasmussen indices

4. **Structural Analysis**
   - Key sector identification
   - Hypothetical extraction
   - Structural decomposition analysis

5. **Comparative Analysis**
   - Time-series changes in structure
   - Cross-country comparisons
   - Structural change metrics

## Known Constraints

[To be updated as constraints are identified]

- **Data availability**: Not all I-O table vintages may be available
- **Format variations**: Different vintages/countries may use different formats
- **Matrix size**: Some I-O tables are very large (100+ sectors)

## Integration Points

### Robin Integration
[To be determined based on I-O tables location in Robin]

### Future Extensions
- Web interface for interactive I-O analysis
- Real-time data updates
- Custom sector aggregations
- Extended I-O models (environmental, social accounting matrix)

## Development Notes

See `PROGRESS_LOG.md` for detailed development history and decisions.

## Testing Strategy

[To be developed]

- Unit tests for all analysis functions
- Validation against published I-O metrics
- Comparison with known results from literature

---

*Created: October 10, 2025*
*Last Updated: October 10, 2025*
