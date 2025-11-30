# VentureValuator
**AI-powered multi-agent system that analyzes startup pitch decks, extracts insights, generates investor memos, financial models, and produces a YC-style pitch deck.**

## The Problem  
Early-stage founders often want to explore the true potential of their ideas — to understand whether the problem is real, whether a market exists, and whether the business is financially viable. At the same time, investors need fast, structured insights to decide whether a startup is worth pursuing. Yet evaluating a startup typically requires extensive research, manual extraction of information from messy pitch decks, careful analysis of traction and unit economics, and the creation of consistent memos or decks. This process is slow, subjective, and error-prone. VentureValuator streamlines this entire workflow, providing quick, data-driven analysis that helps founders validate their ideas and enables investors to assess opportunities efficiently and with confidence.

## The Solution   
VentureValuator streamlines the entire startup-evaluation workflow for both founders and investors. Instead of manually extracting information from pitch decks, researching markets, and building financial models, the tool automates each step — from structured data extraction to financial projections, market analysis, scoring, and memo/deck generation. This reduces hours of work into minutes, enabling founders to quickly test the viability of their ideas and helping investors make faster, more consistent, data-driven decisions.

Upload a startup pitch PDF, and VentureValuator handles everything end-to-end.

## Workflow
VentureValuator processes a pitch deck through a fully automated, end-to-end pipeline:

1. Upload PDF  
   User uploads a pitch deck into the Streamlit UI.

3. Extract Key Information    
   The ExtractionAgent uses Gemini to convert messy PDF text into structured JSON (problem, solution, metrics, competition, etc.).

4. Market Analysis    
   The MarketAgent infers market category, TAM, growth trends, competitors, and opportunities using the extracted data.

5. Financial Modeling      
   A deterministic engine produces revenue projections, CAC/LTV calculations, scenario analysis, and 5-year forecasts—fully transparent and reproducible.

6. Investor Memo Generation    
   The MemoAgent creates a clean, VC-style investment memo with a weighted evaluation score and insights.

7. Pitch Deck Generation    
   The PitchDeckAgent converts outputs into a YC-style 12-slide pitch deck (downloadable as .pptx).

8. Memory & Logging   
   Each run is stored in session logs and a long-term memory bank, allowing users to revisit past analyses.

9. Download & View Outputs       
   Users can download:         
     Memo (PDF/TXT)         
     Pitch deck (PPTX)          
     Full JSON output        

## Architecture
![unnamed](https://github.com/user-attachments/assets/c0ac0a7f-d028-4b0f-a841-c69a3c33e655)

## Tech Stack
1. Python 3.10+
2. Streamlit – UI
3. FPDF – Memo PDF export
4. python-pptx – Pitch deck generation
5. Google Gemini API – LLM extraction + reasoning
6. Custom deterministic scoring engine
7. Memory manager (JSON-based local persistence)

## Installation
### 1. Clone Git Repository
```python
git clone https://github.com/<your-username>/VentureValuator.git
cd VentureValuator
```
### 2. Create & Activate Virtual Environment
macOS/Linux
```python
python3 -m venv venv
source venv/bin/activate
```
Windows
```python
python -m venv venv
venv\Scripts\activate
```
### 3. Install Dependencies
```python
pip install -r requirements.txt
```
### 4. Set-up API Keys
In the root folder, create
```python
.env
```
Inside add,
```python
GEMINI_API_KEY=YOUR_KEY
```
### 5. Ensure Required Folders Exist
```python
mkdir -p memory outputs/decks 
```
### 5. Run the App
```python
streamlit run app/ui.py
```
## Conclusion
VentureValuator isn’t just a tool — it’s a productivity unlock for anyone navigating the uncertain world of early-stage innovation. Founders often feel overwhelmed trying to validate whether their idea truly has market potential, while investors are buried under endless decks that all look the same. By automating extraction, analysis, financial modeling, and memo creation, VentureValuator brings structure to chaos. It turns scattered information into clarity, turns guesswork into grounded insights, and turns hours of effort into minutes.

With every run, users build a deeper understanding of their idea, a clearer narrative, and a more confident decision-making path. VentureValuator empowers people to dream boldly, test intelligently, and move forward with conviction — transforming the messy journey of evaluation into something fast, transparent, and genuinely exciting.

