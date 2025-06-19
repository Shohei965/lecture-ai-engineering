import argparse
import math
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import os
import google.generativeai as genai


def load_questions(path: Path) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def cluster_questions(questions: List[str], model_name: str = "all-MiniLM-L6-v2") -> Dict[int, List[str]]:
    model = SentenceTransformer(model_name)
    embeddings = model.encode(questions)
    n_clusters = max(1, int(math.sqrt(len(questions))))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(embeddings)
    clusters: Dict[int, List[str]] = {}
    for label, question in zip(labels, questions):
        clusters.setdefault(label, []).append(question)
    return clusters


def summarize_clusters(clusters: Dict[int, List[str]]) -> List[str]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")

    summaries = []
    for questions in clusters.values():
        text = " ".join(questions)
        prompt = (
            "Summarize the following questions into one representative question or short summary:\n"
            + text
        )
        response = model.generate_content(prompt)
        summaries.append(response.text.strip())
    return summaries


def main():
    parser = argparse.ArgumentParser(description="Summarize lecture questions")
    parser.add_argument("input", type=Path, help="Text file with one question per line")
    args = parser.parse_args()

    questions = load_questions(args.input)
    if not questions:
        print("No questions found.")
        return

    clusters = cluster_questions(questions)
    summaries = summarize_clusters(clusters)

    for i, summary in enumerate(summaries, 1):
        print(f"\n### Topic {i}\n{summary}")


if __name__ == "__main__":
    main()
