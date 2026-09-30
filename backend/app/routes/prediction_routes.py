from fastapi import APIRouter
from ..schemas import PredictRequest, PredictResponse
from ..ml.predictor import predict_health_condition, get_symptom_catalog

router = APIRouter(prefix="/api/predict", tags=["Health Prediction"])

@router.get("/symptoms")
def get_available_symptoms():
    """Return all available symptoms to populate UI search and selection badges."""
    return {"symptoms": get_symptom_catalog()}

@router.post("/diagnose", response_model=PredictResponse)
def diagnose_condition(req: PredictRequest):
    """
    Processes patient symptoms, runs Bayesian data mining inference,
    predicts the most accurate illness, and recommends required medical scans / lab tests.
    """
    prediction = predict_health_condition(req.symptoms)
    return prediction
