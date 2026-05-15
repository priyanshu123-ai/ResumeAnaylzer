"""
resume_classifier.py — Resume Domain Classifier
=================================================
Scikit-learn pipeline that classifies resumes into professional domains
using TF-IDF + Multinomial Naive Bayes.
"""

import pickle
import os
from typing import Dict, List, Tuple
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
import numpy as np

from backend.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_PATH = Path("backend/models/saved/resume_classifier.pkl")

# ── Training data: (domain_label, sample_keywords) ───────────────────────────
TRAINING_DATA: List[Tuple[str, str]] = [
    ("Data Science", "python pandas numpy scikit-learn machine learning tensorflow keras deep learning statistics regression classification clustering nlp data analysis jupyter matplotlib seaborn"),
    ("Data Science", "data scientist feature engineering model training evaluation metrics cross-validation random forest gradient boosting xgboost lightgbm neural network"),
    ("Software Engineering", "java c++ algorithms data structures object oriented design patterns software architecture unit testing debugging code review pull request"),
    ("Software Engineering", "python java spring boot microservices rest api software developer backend developer full stack agile scrum sprint"),
    ("Frontend Development", "react angular vue javascript typescript html css sass webpack babel responsive design ui ux figma"),
    ("Frontend Development", "frontend developer react hooks redux next.js tailwind css animations web performance lighthouse core web vitals"),
    ("Backend Development", "node.js express django flask fastapi python rest api graphql postgresql mysql mongodb redis authentication jwt"),
    ("Backend Development", "backend developer api design database optimization server-side rendering caching microservices docker kubernetes"),
    ("DevOps/Cloud", "aws gcp azure docker kubernetes terraform ansible jenkins github actions ci cd pipeline infrastructure as code"),
    ("DevOps/Cloud", "devops engineer cloud architect site reliability engineer sre monitoring prometheus grafana elk stack linux bash scripting"),
    ("Data Engineering", "apache spark hadoop kafka airflow etl pipeline data warehouse bigquery snowflake redshift data lake"),
    ("Data Engineering", "data engineer spark streaming sql optimization schema design data modeling dbt transformation"),
    ("Cybersecurity", "penetration testing vulnerability assessment security audit siem firewall network security iso 27001 ethical hacking"),
    ("Cybersecurity", "cybersecurity analyst threat detection incident response forensics malware analysis security operations center soc"),
    ("Machine Learning", "computer vision nlp transformer bert gpt attention mechanism fine-tuning hugging face model deployment mlops"),
    ("Machine Learning", "machine learning engineer feature store model registry a/b testing hyperparameter tuning experiment tracking mlflow"),
    ("Product Management", "product roadmap stakeholder management agile user stories sprint planning okr kpi product strategy go-to-market"),
    ("Business Analysis", "business analyst requirements gathering process improvement workflow data visualization power bi tableau sql"),
    ("Design/UX", "figma sketch adobe xd ux research wireframing prototyping user testing design system accessibility heuristic evaluation"),
    ("Full Stack", "react node.js python django postgresql mongodb docker aws full stack developer end-to-end feature development"),
]


class ResumeClassifier:
    """
    Scikit-learn pipeline for resume domain classification.
    Uses TF-IDF vectorization + Multinomial Naive Bayes.
    """

    def __init__(self):
        self.pipeline: Pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=3000,
                stop_words="english",
                min_df=1,
            )),
            ("clf", MultinomialNB(alpha=0.1)),
        ])
        self.label_encoder = LabelEncoder()
        self.is_trained = False
        self._auto_train()

    def _auto_train(self):
        """Train on built-in training data at startup."""
        try:
            texts = [text for _, text in TRAINING_DATA]
            labels = [label for label, _ in TRAINING_DATA]
            encoded = self.label_encoder.fit_transform(labels)
            self.pipeline.fit(texts, encoded)
            self.is_trained = True
            logger.info(
                f"[OK] Resume classifier trained on {len(texts)} samples "
                f"({len(set(labels))} classes)"
            )
        except Exception as e:
            logger.error(f"Classifier training failed: {e}")

    def predict(self, resume_text: str) -> Dict:
        """
        Predict the professional domain of a resume.

        Args:
            resume_text: Full resume text.

        Returns:
            Dict with predicted class and confidence scores.
        """
        if not self.is_trained:
            return {"domain": "Unknown", "confidence": 0.0, "all_scores": {}}

        try:
            # Get probability distribution across all classes
            proba = self.pipeline.predict_proba([resume_text[:2000]])[0]
            classes = self.label_encoder.classes_

            # Top prediction
            top_idx = int(np.argmax(proba))
            domain = classes[top_idx]
            confidence = round(float(proba[top_idx]) * 100, 1)

            # All class scores sorted descending
            all_scores = {
                cls: round(float(p) * 100, 1)
                for cls, p in sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)
            }

            logger.debug(f"Classified as '{domain}' with {confidence}% confidence")
            return {
                "domain": domain,
                "confidence": confidence,
                "all_scores": all_scores,
            }
        except Exception as e:
            logger.error(f"Classification prediction failed: {e}")
            return {"domain": "Software Engineering", "confidence": 50.0, "all_scores": {}}


# ── Singleton instance ────────────────────────────────────────────────────────
_classifier_instance: ResumeClassifier = None


def get_classifier() -> ResumeClassifier:
    """Return singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ResumeClassifier()
    return _classifier_instance


def classify_resume(resume_text: str) -> Dict:
    """Convenience function — classify a resume text."""
    return get_classifier().predict(resume_text)
