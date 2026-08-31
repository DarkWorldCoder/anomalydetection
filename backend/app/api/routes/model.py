from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.responses import success_response
from app.models.user import User
from app.services.detection_service import load_artifacts

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/info")
async def model_info(_: User = Depends(get_current_user)):
    config, model = load_artifacts()
    data = {
        "name": config["model_name"],
        "dataset": config["dataset_name"],
        "status": "loaded",
        "feature_count": len(config["feature_names"]),
        "features": config["feature_names"],
        "threshold": config["threshold"],
        "trees": len(model["trees"]),
        "sample_size": model["sample_size"],
        "validation_metrics": config["validation_metrics"],
        "test_metrics": config["test_metrics"],
    }
    return success_response("Model information fetched", data)
