import joblib
import torch
import numpy as np
import uuid
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import RobertaTokenizer, RobertaModel

class NLPService:
    def __init__(self):
        # Load the models
        try:
            self.model = joblib.load('models/xgboost_roberta_best.pkl')
            self.le = joblib.load('models/label_encoder.pkl')
            print("Successfully loaded XGBoost Model and Label Encoder.")
        except Exception as e:
            print(f"Error loading models: {e}")
            self.model = None
            self.le = None

        # Load RoBERTa for embeddings
        self.tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
        self.roberta = RobertaModel.from_pretrained('roberta-base')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.roberta = self.roberta.to(self.device)
        self.roberta.eval()
        
        # Load Sentiment Analyzer
        self.analyzer = SentimentIntensityAnalyzer()

        # Keywords for Priority & Urgency mapping
        self.high_urgency_keywords = ['immediate', 'urgent', 'emergency', 'asap', 'broken', 'down', 'dead', 'now', 'cancel']

    def _extract_roberta_features(self, text):
        inputs = self.tokenizer([text], padding=True, truncation=True, max_length=128, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.roberta(**inputs)
        cls_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        return cls_embeddings

    def classify_complaint(self, text: str) -> str:
        if self.model is None or self.le is None:
            return "Unknown"
        
        features = self._extract_roberta_features(text)
        pred_probs = self.model.predict_proba(features)[0] # Softprob
        pred_idx = np.argmax(pred_probs)
        category = self.le.inverse_transform([pred_idx])[0]
        return category

    def analyze_sentiment(self, text: str) -> dict:
        vader_scores = self.analyzer.polarity_scores(text)
        compound = vader_scores['compound']
        
        if compound >= 0.05:
            sentiment_label = "Positive"
        elif compound <= -0.05:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"

        return {
            "score": compound,
            "label": sentiment_label
        }

    def determine_urgency_and_priority(self, text: str, sentiment_score: float) -> dict:
        text_lower = text.lower()
        
        # Check for urgent keywords
        has_urgent_keywords = any(kw in text_lower for kw in self.high_urgency_keywords)
        
        # Heuristic rules combining sentiment and keywords
        if has_urgent_keywords and sentiment_score <= -0.5:
            priority = "Critical"
            urgency = True
        elif has_urgent_keywords or sentiment_score <= -0.7:
            priority = "High"
            urgency = True
        elif sentiment_score < 0:
            priority = "Medium"
            urgency = False
        else:
            priority = "Low"
            urgency = False
            
        return {
            "urgency": urgency,
            "priority": priority
        }

    def determine_routing_and_sla(self, category: str, priority: str) -> dict:
        # Department Routing mapping
        routing_map = {
            "Billing": "Finance Department",
            "Account": "Customer Accounts",
            "Product": "Product Management",
            "Service": "Customer Service",
            "Delivery": "Logistics & Delivery",
            "Network Problem": "Technical Support", 
            "Data Speed": "Technical Support",
            "International Roaming": "Network Routing",
            "Dropped Calls": "Technical Support"
        }
        
        department = routing_map.get(category, "General Support")

        # SLA Tracking mapping based on priority
        sla_map = {
            "Critical": "2 Hours",
            "High": "12 Hours",
            "Medium": "24 Hours",
            "Low": "48 Hours"
        }
        
        sla = sla_map.get(priority, "24 Hours")
        
        return {
            "department": department,
            "sla": sla
        }

    def process_full_complaint(self, text: str, customer_name: str, customer_email: str) -> dict:
        category = self.classify_complaint(text)
        sentiment = self.analyze_sentiment(text)
        urg_pri = self.determine_urgency_and_priority(text, sentiment["score"])
        routing_sla = self.determine_routing_and_sla(category, urg_pri["priority"])

        complaint_id = f"CMP-{str(uuid.uuid4())[:8].upper()}"

        return {
            "complaint_id": complaint_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "text": text,
            "category": category,
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "urgency": urg_pri["urgency"],
            "priority": urg_pri["priority"],
            "department": routing_sla["department"],
            "sla": routing_sla["sla"],
            "status": "Open",
            "created_at": datetime.now().isoformat()
        }

nlp_service_instance = NLPService()
