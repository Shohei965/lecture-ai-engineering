# Final Assignment: Lecture Q&A Summarizer

This directory contains a simple prototype system for summarizing a large number of questions collected during a lecture. The goal is to help instructors answer related questions together and reduce their workload while keeping student satisfaction high.

## Overview
1. Questions are clustered by semantic similarity using sentence embeddings.
2. Each cluster is summarized using Google's Gemini API to produce a representative question or summary.
3. These summaries can then be answered by the lecturer in bulk.

The system is designed to handle up to around 1000 questions in a single run.

## Requirements
- Python 3.10 or later
- See `requirements.txt` for required packages

Install dependencies with:
```bash
pip install -r requirements.txt
```

Set your Gemini API key in the environment:
```bash
export GOOGLE_API_KEY="<YOUR_API_KEY>"
```

## Usage
Prepare a text file containing one question per line (see `sample_questions.txt` for an example), then run:
```bash
python summarize.py questions.txt
```
The script outputs summaries for each cluster of related questions. Summaries are generated using Gemini, so an internet connection and a valid API key are required.

## Notes
- This is a minimal prototype. In a production setting you may want a more advanced clustering algorithm and better control over the summarization model.
- Gemini API calls may incur latency or quota limits depending on your account.

## Using Google Sheets
Questions can also be fetched directly from a Google Sheet. Provide a service account credentials JSON and run:
```bash
python sheets_summarize.py SHEET_ID "Sheet1!A:A" path/to/credentials.json
```
This will read the specified column from the sheet, cluster the questions, and output representative topics generated with Gemini.
