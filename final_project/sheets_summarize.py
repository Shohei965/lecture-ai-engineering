import argparse
from pathlib import Path
from typing import List, Dict
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai
from sklearn.cluster import KMeans
import numpy as np


def fetch_questions(sheet_id: str, range_: str, creds_file: str) -> List[str]:
    """Fetch questions from a Google Sheet range."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = service_account.Credentials.from_service_account_file(creds_file, scopes=scopes)
    service = build("sheets", "v4", credentials=creds)
    resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_).execute()
    values = resp.get("values", [])
    # flatten and filter empty strings
    return [row[0].strip() for row in values if row and row[0].strip()]


def embed_questions(questions: List[str], model: str = "models/embedding-001") -> np.ndarray:
    """Get embeddings for each question using Gemini."""
    return np.array([
        genai.embed_content(model=model, content=q)["embedding"]
        for q in questions
    ])


def cluster_questions(questions: List[str], n_clusters: int) -> Dict[int, List[str]]:
    """Cluster questions using KMeans."""
    embeddings = embed_questions(questions)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(embeddings)
    clusters: Dict[int, List[str]] = {}
    for label, question in zip(labels, questions):
        clusters.setdefault(label, []).append(question)
    return clusters


def summarize_cluster(model, questions: List[str]) -> str:
    text = " \n".join(questions)
    prompt = (
        "あなたは講義担当教員です。以下の質問をまとめて代表質問を作成し、その回答を日本語で200字以内で出力してください:\n" + text
    )
    resp = model.generate_content(prompt)
    return resp.text.strip()


def process_sheet(sheet_id: str, range_: str, creds_file: str) -> None:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not set")
    genai.configure(api_key=api_key)
    questions = fetch_questions(sheet_id, range_, creds_file)
    if not questions:
        print("No questions found.")
        return
    n_clusters = max(1, int(len(questions) ** 0.5))
    clusters = cluster_questions(questions, n_clusters)
    model = genai.GenerativeModel("gemini-pro")
    for i, qs in clusters.items():
        summary = summarize_cluster(model, qs)
        print(f"\n### Topic {i + 1}\n{summary}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize questions from Google Sheets")
    parser.add_argument("sheet_id", help="Spreadsheet ID")
    parser.add_argument("range", help="Range like Sheet1!A:A")
    parser.add_argument("credentials", type=Path, help="Path to service account JSON")
    args = parser.parse_args()
    process_sheet(args.sheet_id, args.range, str(args.credentials))
