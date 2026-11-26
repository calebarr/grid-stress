# Grid Stress and Data Center Growth

University of Michigan
Master of Applied Data Science
SIADS 699 - Capstone Project

## Project Overview

This project investigates the relationship between data
center growth and electrical grid stress, with a focus
on the PJM Interconnection and the Dominion (DOM) region.

The study uses historical electricity demand, generation
outage forecasts, congestion prices, weather, and data
center capacity information to examine grid conditions
from 2020 through 2024.

## Research Questions

1. Can electrical grid stress be measured using publicly
   available electricity data?

2. Does data center growth contribute measurable
   information about grid stress after accounting for
   weather, electricity demand, and other relevant factors?

3. Can periods of high electrical grid stress be predicted?

## Data Sources

### PJM Data Miner 2

The historical electricity data pipeline covers
January 2020 through December 2024.

| Dataset | API Endpoint | Description |
|---|---|---|
| Hourly Metered Load | 'hrl_load_metered' | Hourly electricity demand |
| Generation Outages | 'gen_outages_by_type' | Forecasted generation outages |
| Real-Time Hourly LMP | 'rt_hrl_lmps' | Zone-level electricity prices and congestion components |

Source: https://dataminer2.pjm.com/

### Additional Research Data

- Historical weather observations
- Data center locations
- Data center operational dates
- Reported data center capacity

These additional datasets support the research analysis
and are not currently integrated into the PJM ingestion
pipeline.

### Data Limitations

- Reported data center capacity does not necessarily
  represent actual electricity consumption.
- Data center locations may not align precisely with
  PJM regional boundaries.
- Generation outage forecasts do not necessarily
  represent realized generation outages.
- Statistical association do not establish causation.

## Repository Structure

'''text
grid-stress/
|- data/
|  |-- raw/
|  |-- interim/
|  |-- processed/
|-- docs/
|-- notebooks/
|-- reports/
|   |__ figures/
|-- src/
|   |-- cleaning/
|   |-- ingestion/
|   |-- utils/
|-- .env.example
|-- .gitignore
|-- main.py
|-- README.md
|__ requirements.txt
'''

### Directory Responsibilities

- 'data/raw/' - Original, unmodified source data.
- 'data/interim/' - Intermediate and combined datasets.
- 'data/processed/' - Analysis-ready datasets.
- 'docs/' - Project documentation.
- 'notebooks/' - Exploratory analysis, statistical
  analysis, and predictive modeling.
- 'reports/' - Data audit reports and research results.
- 'reports/figures/' - Project visualizations.
- 'src/ingestion/' - PJM API data acquisition modules.
- 'src/utils/' - Shared utility functions.

### Configuration and Execution

- 'main.py' - Central entry point for the PJM pipeline.
- 'requirements.txt' - Python package dependencies.
- '.env.example' - Environment configuration template.
- '.gitignore' - Excludes credentials, local settings,
   and datasets from version control.

Raw, intermediate, and processed datasets are stored
locally or externally and are not committed to Github.
Storage locations are configured through environment
variables.

## Getting Started

### Prerequisites

- Python 3
- Git
- PJM Data Miner 2 API access
- Sufficient storage for historical PJM datasets

### 1. Clone the Repository

''' bash
git clone https://github.com/grid-stress.git
cd grid-stress
'''

### 2. Create a Virtual Environment

'''bash
python3 -m venv .venv
'''

Activate the environment on macOS or Linux:

'''bash
source .venv/bin/activate
'''

For Windows Poweshell:

'''powershell
.venv\Scripts\Activate.ps1
'''

### 3. Install Dependencies

'''bash
pip install -r requirements.txt
'''

### 4. Configure Environment Variables

Create a local '.env. file using '.env.example'
as a template.

'''dotenv
PJM_API_KEY=your_pjm_api_key_here
GRID_STRESS_RAW_DIR=/path/to/grid-stress-data/raw/pjm_load
'''

Replace the placeholder values with your own PJM API
key and preferred data storage location.


Never commit the '.env' file or share API credentials
through GitHub.

### 5. Verify Installation

'''bash
python main.py --help
'''

This displays the available pipeline commands without
downloading or modifying any datasets.

# Running the Pipeline

Download historical PJM datasets:

'''bash
python main.py --download
'''

Audit existing datasets:

'''bash
python main.py --combine
'''

Audit and combine historical datasets:

'''bash
python main.py --comhine
'''

The team stores historical PJM datasets in a shared
University of Michigan Google Drive folder. storage
paths are configured through the local '.env' file.

Team members with access to the existing datasets
do not need to download them again.

Audit reports are saved in 'reports/'.

The download stage checks existing monthly files before
requesting data. The combination stage requires the
data audits to pass before proceeding.

Running 'python main.py' without arguments displays
the available commands.