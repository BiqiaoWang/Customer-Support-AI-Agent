## 🤖Customer Support AI Agent
This is a three-person summer school project. 
We developed an AI agent to analyse customer support tickets, categorise customer issues, prioritise requests, and generate tailored responses.

## 👩‍💻My Contributions (Ava Wang)
As part of this three-person project, I was primarily responsible for:

- Designed an AI-agent escalation workflow for customer support tickets.
- Implemented and evaluated multiple LLMs for sentiment classification.
- Built a human-annotated gold-standard dataset and VADER baseline for model evaluation.
- Collected, cleaned, and preprocessed customer support ticket datasets using Python.

#### 📌Note: My contributions are organised under the *My_contributions* folder📁 in this repository.
---
👇 The following sections present my contributions to this project.
---
## Project Workflow
<img width="1086" height="1448" alt="Overall workflow" src="https://github.com/user-attachments/assets/e740bd28-ae10-4b1e-866f-37c582bef0b8" />

## AI Agent Escalation Workflow
<img width="4254" height="4092" alt="AI Agent Escalation Workflow" src="https://github.com/user-attachments/assets/3236f082-25dd-413a-b289-01d089e24071" />

## Data Cleaning
During data cleaning, we found that the ticket descriptions contained non-standard text, including:

- Non-English symbols and special characters
- HTML tags (e.g., `<br/>`)
- Line breaks (\n, \\n)
- Extra spaces

To prepare the data for sentiment classification, the following preprocessing steps were applied:

1. Replaced newline characters with spaces.
2. Removed HTML tags.
3. Converted all text to lowercase.
4. Removed abnormal characters while preserving English letters, numbers, and common punctuation.
5. Removed unnecessary and duplicate spaces.

> **Note:** Traditional NLP preprocessing (e.g., stop word removal, tokenisation, and lemmatisation) was not applied. The original sentence structure was preserved because LLMs rely on contextual information for sentiment classification.


## Sentiment Classification Pipeline

```text
Customer Support Tickets
          │
          ▼
Data Preprocessing
          │
          ▼
Gold Standard Construction
(Stratified Sampling + Manual Annotation)
          │
          ▼
VADER Baseline
          │
          ▼
LLM Evaluation
(Llama 3.1 vs Llama 3.3)
          │
          ▼
Performance Evaluation
(Precision • Recall • F1-score)
```

## Model Evaluation Workflow
The following workflow summarises the data processing and model evaluation process.
```
customer_support_tickets.csv
          │
          ▼
01_data_preprocessing.py
          │
          ▼
combined_tickets_clean_text.csv
          │
          ▼
02_gold_standard_sampling_and_vader_baseline.py
          │
          ▼
gold_set_stratified_by_ticket_type.csv
          │
          ▼
Manual annotation
          │
          ▼
gold_set_labeled.csv
          ├──────────────┐
          ▼              ▼
vader_predictions.csv    03_sentiment_classification_and_llm_evaluation.py
                             │
                             ▼
                         outputs/
                         ├── gold_set_with_llm_labels.csv
                         ├── vader_predictions.csv
                         ├── llama31_predictions.csv
                         ├── llama33_predictions.csv
                         └── metrics_comparison.txt
```

## Evaluation Metrics
The models were evaluated using a manually labelled gold-standard dataset.

Evaluation metrics:
- Recall (Negative)
- Precision (Negative)
- F1-score (Negative)

Since this sentiment classification was developed for a customer support AI-Agent, the objective was to **identify negative tickets** that should be prioritised for escalation to human agents. Therefore, a **binary sentiment classification (Negative vs. Non-Negative)** was adopted, and the evaluation focused on the negative class using Recall, Precision, and F1-score.

### Results 
<img width="869" height="181" alt="image" src="https://github.com/user-attachments/assets/d9b760cd-89b4-4a3f-86d3-dea7d2ab76b4" />

### Skills
- Python | Pandas | LLM | Prompt Engineering | Sentiment Classification | Data Preprocessing | Gold-standard Dataset Construction | Model Evaluation

