# AI Complaint Classification System (Offline Enterprise Edition)

An end-to-end Machine Learning web application designed to automatically triage, classify, and route customer complaints for enterprise telecom and logistics sectors using a fine-tuned Hugging Face **RoBERTa** Transformer model.

## 🚀 Key Features

* **Deep Learning NLP Triage:** Replaces manual human routing with an automated RoBERTa architecture achieving **~85% F1-score**, fine-tuned exclusively on augmented corporate telecom datasets.
* **Human-in-the-Loop Safe AI:** Implements a strict mathematical 65% Confidence Threshold. Any ambiguous or "gibberish" tickets scoring below this threshold bypass the AI and are forced into a "Pending Manual Review" queue for human assignment.
* **100% Offline Capability:** Operates flawlessly on secure, air-gapped internal corporate intranets. The PyTorch NLP models, SQLite database, and CSS Webfonts (Inter) are entirely locally hosted, requiring zero external internet API calls.
* **Dual-Database Synchronization:** Combines a secure `SQLite` backend (for Customer Portal transparency and fast lookups) physically synchronized with `.csv` files (used as legacy ledgers by individual departments).
* **Role-Based Command Centers:** 
  * **Admin UI:** Live KPI dashboards, active ticket trackers, and manual reassignment workflows.
  * **Customer UI:** Secure history portal tracking ticket statuses and 24-48 hr SLAs.

## 🧠 Machine Learning Architecture

The core routing engine utilizes a hybrid approach:

1. **Deterministic Heuristic Override:** High-fidelity business-critical keywords (e.g. `tracking`, `router`, `overcharged`) mandate primary classification to ensure 100% accuracy on explicit edge cases.
2. **RoBERTa Transformer Pipeline:** For nuanced natural language, the query is passed through an offline HuggingFace pipeline powered by PyTorch `best_model_iter2`. The model evaluates 128-token lengths against 5 target departments (Account, Billing, Delivery, Product, Service).
3. **Vader Sentiment Urgency Scanner:** Analyzes emotional polarity (e.g., heavily negative compound scores) to automatically calculate Priority and SLAs (e.g., 2 Hours vs 48 Hours).

## 🛠️ Technology Stack
* **AI/ML:** PyTorch, Hugging Face Transformers, NLTK, VaderSentiment
* **Backend:** Python 3.10+, FastAPI, Uvicorn, SQLite3, Pydantic
* **Frontend:** Vanilla JavaScript, HTML5, Vanilla CSS

## ⚙️ Installation & Running Offline

### 1. Requirements
* Python 3.10+
* Git
* Note: The `best_model_iter2` directory is intentionally ignored by GitHub due to its >400MB file size. To run predictions, the fine-tuned RoBERTa PyTorch weights must be manually downloaded and placed in the `/models/best_model_iter2` directory.

### 2. Environment Setup
```bash
# Clone repository
git clone https://github.com/saikiran-18/project_pr1.git
cd project_pr1

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch the Servers
The system requires both the Python API and a frontend HTTP server.

**Terminal 1 (Backend API):**
```bash
cd backend
uvicorn main:app --reload
```
*The FastAPI backend will boot on `http://127.0.0.1:8000`*

**Terminal 2 (Frontend UI):**
```bash
cd frontend
python -m http.server 5500
```
*The web portal will boot on `http://127.0.0.1:5500`*

---
*Built a end-to-end Enterprise AI deployment topologies.*
