// Google Apps Script for summarizing lecture questions with Gemini
// Place this script in the Google Sheets Apps Script editor.

const API_BASE = 'https://generativelanguage.googleapis.com/v1beta';

function getApiKey() {
  const key = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!key) throw new Error('Set GEMINI_API_KEY in script properties.');
  return key;
}

function onOpen() {
  SpreadsheetApp.getActiveSpreadsheet()
    .addMenu('Q&A Tools', [{name: 'Summarize Questions', functionName: 'summarizeQuestions'}]);
}

function summarizeQuestions() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheets()[0];
  const lastRow = sheet.getLastRow();
  const values = sheet.getRange(2, 2, lastRow - 1).getValues().flat(); // column B
  const questions = values.filter(q => q);
  if (!questions.length) return;

  const embeddings = questions.map(q => embedText(q));
  const k = Math.ceil(Math.sqrt(questions.length));
  const result = kmeans(embeddings, k, 6);
  const clusters = {};
  result.labels.forEach((label, i) => {
    (clusters[label] = clusters[label] || []).push(questions[i]);
  });

  const ordered = Object.entries(clusters)
    .sort((a, b) => b[1].length - a[1].length);

  let summarySheet = ss.getSheetByName('QA Summary');
  if (summarySheet) ss.deleteSheet(summarySheet);
  summarySheet = ss.insertSheet('QA Summary');
  summarySheet.appendRow(['Priority', 'Representative QA', 'Count']);

  ordered.forEach(([label, qs], idx) => {
    const text = qs.join('\n');
    const prompt = '以下の学生質問をまとめて代表質問と簡潔な回答を日本語で作成してください。\n' + text;
    const summary = generateText(prompt);
    summarySheet.appendRow([idx + 1, summary, qs.length]);
  });

  addWordCloud(summarySheet, questions);
}

function embedText(text) {
  const url = `${API_BASE}/models/embedding-001:embedContent?key=${getApiKey()}`;
  const payload = {content: {parts: [{text}]}};
  const res = UrlFetchApp.fetch(url, {method: 'post', contentType: 'application/json', payload: JSON.stringify(payload)});
  const data = JSON.parse(res.getContentText());
  return data.embedding.values;
}

function generateText(prompt) {
  const url = `${API_BASE}/models/gemini-pro:generateContent?key=${getApiKey()}`;
  const payload = {contents: [{parts: [{text: prompt}]}]};
  const res = UrlFetchApp.fetch(url, {method: 'post', contentType: 'application/json', payload: JSON.stringify(payload)});
  const data = JSON.parse(res.getContentText());
  return data.candidates[0].content.parts[0].text.trim();
}

function addWordCloud(sheet, questions) {
  const freq = {};
  questions.forEach(q => q.split(/\s+/).forEach(w => {
    w = w.replace(/[\p{P}\p{S}]/gu, '').toLowerCase();
    if (w) freq[w] = (freq[w] || 0) + 1;
  }));
  const data = Charts.newDataTable()
    .addColumn(Charts.ColumnType.STRING, 'Word')
    .addColumn(Charts.ColumnType.NUMBER, 'Count');
  Object.entries(freq).forEach(([w, c]) => data.addRow([w, c]));
  const chart = Charts.newBarChart()
    .setDataTable(data)
    .setTitle('Word Frequencies')
    .setDimensions(600, 400)
    .build();
  sheet.insertChart(chart);
}

function kmeans(vectors, k, iters) {
  const n = vectors.length;
  const dims = vectors[0].length;
  let centroids = [];
  for (let i = 0; i < k; i++) {
    centroids.push(vectors[Math.floor(Math.random() * n)].slice());
  }
  let labels = new Array(n).fill(0);
  for (let t = 0; t < iters; t++) {
    for (let i = 0; i < n; i++) {
      let best = 0; let minD = Infinity;
      for (let j = 0; j < k; j++) {
        const d = distance2(vectors[i], centroids[j]);
        if (d < minD) { minD = d; best = j; }
      }
      labels[i] = best;
    }
    let sums = Array.from({length: k}, () => Array(dims).fill(0));
    let counts = Array(k).fill(0);
    for (let i = 0; i < n; i++) {
      counts[labels[i]]++;
      for (let d = 0; d < dims; d++) sums[labels[i]][d] += vectors[i][d];
    }
    for (let j = 0; j < k; j++) {
      if (counts[j]) centroids[j] = sums[j].map(x => x / counts[j]);
    }
  }
  return {centroids, labels};
}

function distance2(a, b) {
  let sum = 0;
  for (let i = 0; i < a.length; i++) {
    const diff = a[i] - b[i];
    sum += diff * diff;
  }
  return sum;
}
