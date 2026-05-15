"""
skill_predictor.py — Skill Prediction System
=============================================
Predicts skills a candidate should have or learn based on job role
and current skill set. Uses a curated skill adjacency graph.
"""

from typing import Dict, List, Set
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ── Skill adjacency map: role → (essential skills, advanced skills) ───────────
ROLE_SKILLS: Dict[str, Dict[str, List[str]]] = {
    "Data Science": {
        "essential": ["Python","Pandas","NumPy","Matplotlib","Scikit-learn","SQL","Statistics","Jupyter"],
        "advanced": ["TensorFlow","PyTorch","Deep Learning","Spark","Feature Engineering","MLOps","Kafka"],
        "certifications": ["Google Professional Data Engineer","AWS Machine Learning Specialty","IBM Data Science"],
    },
    "Software Engineering": {
        "essential": ["Python","Java","Data Structures","Algorithms","Git","REST API","SQL","Testing"],
        "advanced": ["System Design","Microservices","Kubernetes","Design Patterns","CI/CD","GraphQL"],
        "certifications": ["AWS Developer Associate","Google Associate Cloud Engineer","Oracle Java SE"],
    },
    "Frontend Development": {
        "essential": ["HTML","CSS","JavaScript","React","TypeScript","Git","Responsive Design","REST API"],
        "advanced": ["Next.js","Redux","GraphQL","WebAssembly","Performance Optimization","Testing Library"],
        "certifications": ["Meta Frontend Developer","Google UX Design","AWS CloudFront"],
    },
    "Backend Development": {
        "essential": ["Python","Node.js","REST API","SQL","NoSQL","Authentication","Docker","Git"],
        "advanced": ["Microservices","Message Queues","Redis","Elasticsearch","GraphQL","Kubernetes"],
        "certifications": ["AWS Developer Associate","MongoDB Certified Developer","Node.js Application Developer"],
    },
    "DevOps/Cloud": {
        "essential": ["Linux","Docker","Kubernetes","AWS/GCP/Azure","CI/CD","Terraform","Bash","Git"],
        "advanced": ["Ansible","Prometheus","Grafana","Helm","Istio","GitOps","Infrastructure as Code"],
        "certifications": ["AWS Solutions Architect","CKA (Kubernetes)","HashiCorp Terraform Associate"],
    },
    "Machine Learning": {
        "essential": ["Python","TensorFlow","PyTorch","Scikit-learn","NumPy","Pandas","Linear Algebra"],
        "advanced": ["Transformers","MLOps","Kubeflow","Feature Stores","Model Deployment","Experiment Tracking"],
        "certifications": ["DeepLearning.AI TensorFlow Developer","AWS ML Specialty","Google ML Engineer"],
    },
    "Data Engineering": {
        "essential": ["Python","SQL","Apache Spark","Airflow","ETL","Data Warehousing","Git","Linux"],
        "advanced": ["Kafka","dbt","Flink","Delta Lake","Iceberg","Data Mesh","Cloud Data Platforms"],
        "certifications": ["Databricks Certified Engineer","Google Professional Data Engineer","Snowflake SnowPro"],
    },
    "Full Stack": {
        "essential": ["JavaScript","React","Node.js","Python","SQL","Docker","Git","REST API"],
        "advanced": ["TypeScript","Next.js","GraphQL","Redis","Kubernetes","CI/CD","System Design"],
        "certifications": ["Meta Full Stack Developer","AWS Developer","MongoDB Certified Developer"],
    },
    "Cybersecurity": {
        "essential": ["Network Security","Linux","Python","Firewalls","SIEM","Vulnerability Assessment"],
        "advanced": ["Penetration Testing","Threat Hunting","SOAR","Zero Trust","Cloud Security","Forensics"],
        "certifications": ["CompTIA Security+","CEH","CISSP","OSCP","AWS Security Specialty"],
    },
    "Product Management": {
        "essential": ["Agile","Scrum","User Stories","Roadmapping","SQL","Data Analysis","Communication"],
        "advanced": ["OKRs","A/B Testing","Product Analytics","Design Thinking","Stakeholder Management"],
        "certifications": ["Certified Scrum Product Owner","PMP","Google Project Management"],
    },
}


def predict_missing_skills(
    current_skills: List[str],
    job_role: str
) -> Dict[str, List[str]]:
    """
    Predict which skills a candidate is missing for a given role.

    Args:
        current_skills: Skills already on the resume.
        job_role: Target job role (from classifier or user input).

    Returns:
        Dict with 'missing_essential', 'missing_advanced', 'certifications'.
    """
    # Normalize for comparison
    current_lower: Set[str] = {s.lower() for s in current_skills}

    # Find best matching role key
    matched_role = _match_role(job_role)
    role_data = ROLE_SKILLS.get(matched_role, ROLE_SKILLS["Software Engineering"])

    essential = role_data.get("essential", [])
    advanced = role_data.get("advanced", [])
    certs = role_data.get("certifications", [])

    missing_essential = [
        s for s in essential
        if s.lower() not in current_lower
    ]
    missing_advanced = [
        s for s in advanced
        if s.lower() not in current_lower
    ]

    logger.debug(
        f"Skill prediction for '{matched_role}': "
        f"{len(missing_essential)} essential missing, "
        f"{len(missing_advanced)} advanced missing"
    )

    return {
        "role": matched_role,
        "current_skills": current_skills[:20],
        "missing_essential": missing_essential[:8],
        "missing_advanced": missing_advanced[:8],
        "certifications": certs[:3],
        "match_percentage": _calc_skill_match(current_lower, essential),
    }


def _match_role(job_role: str) -> str:
    """Find the closest matching role key in ROLE_SKILLS."""
    if not job_role:
        return "Software Engineering"
    role_lower = job_role.lower()
    for key in ROLE_SKILLS.keys():
        if key.lower() in role_lower or role_lower in key.lower():
            return key
    # Keyword fallback
    if any(k in role_lower for k in ["data sci", "analyst"]):
        return "Data Science"
    if any(k in role_lower for k in ["front", "ui", "react", "angular"]):
        return "Frontend Development"
    if any(k in role_lower for k in ["back", "api", "django", "flask"]):
        return "Backend Development"
    if any(k in role_lower for k in ["devops", "cloud", "sre", "platform"]):
        return "DevOps/Cloud"
    if any(k in role_lower for k in ["machine", "ml ", "ai ", "deep"]):
        return "Machine Learning"
    if any(k in role_lower for k in ["full stack", "fullstack"]):
        return "Full Stack"
    return "Software Engineering"


def _calc_skill_match(current_lower: Set[str], essential: List[str]) -> float:
    """Calculate percentage of essential skills already possessed."""
    if not essential:
        return 0.0
    matched = sum(1 for s in essential if s.lower() in current_lower)
    return round(matched / len(essential) * 100, 1)
