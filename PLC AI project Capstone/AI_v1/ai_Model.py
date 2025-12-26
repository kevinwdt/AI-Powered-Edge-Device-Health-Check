# ai_model.py
# Kevin Model

import os
import pickle
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from base_Service import BaseService


@dataclass
class TrainedArtifacts:
    scaler: MinMaxScaler
    model: RandomForestClassifier
    feature_names: List[str]           # order of features at train time
    label_names: Dict[int, str]        # e.g. {0:"Healthy",1:"Warning",2:"Critical"}


class AIModel(BaseService):
    """
    AIModel service
    - Train on simulated/historical telemetry-like rows
    - Save scaler+model into model.pkl
    - Load model on start
    - Predict label + reason

    Labels: Healthy / Warning / Critical
    """

    def __init__(self, model_path: str = "model.pkl"):
        super().__init__("AIModel")
        self.model_path = model_path
        self.artifacts: TrainedArtifacts | None = None

    # ----------------------------
    # Lifecycle (keep original)
    # ----------------------------
    def start(self) -> None:
        super().start()
        if os.path.exists(self.model_path):
            self.artifacts = self._load_artifacts(self.model_path)
            print(f"[AIModel] Loaded model from {self.model_path}")
        else:
            print("[AIModel] No existing model found yet. Train first.")

    def stop(self) -> None:
        super().stop()

    # ----------------------------
    # TRAINING
    # ----------------------------
    def train_from_rows(
        self,
        rows: List[Dict[str, Any]],
        feature_keys: List[str],
        label_key: str,
        test_size: float = 0.3,
        random_state: int = 42,
        n_estimators: int = 300,
        max_depth: int | None = None,
        class_weight: str | Dict[str, float] | None = "balanced"
    ) -> Dict[str, Any]:
        """
        Train RandomForest on labeled rows.

        rows example:
          {
            "used_memory": 1200.5,
            "used_storage": 3600.2,
            "cpuusage": 55.0,
            "temperature": 48.0,
            "label": "Healthy"
          }
        """

        X_list: List[List[float]] = []
        y_list: List[int] = []
        label_to_id: Dict[str, int] = {}
        next_id = 0

        for r in rows:
            # features in fixed order
            feats = []
            for k in feature_keys:
                v = r.get(k, 0.0)
                # If missing/None/NaN -> 0.0 (you can change strategy later)
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    v = 0.0
                feats.append(float(v))
            X_list.append(feats)

            raw_label = r.get(label_key, "Healthy")
            if raw_label not in label_to_id:
                label_to_id[raw_label] = next_id
                next_id += 1
            y_list.append(label_to_id[raw_label])

        X = np.array(X_list, dtype=float)
        y = np.array(y_list, dtype=int)

        id_to_label = {i: name for (name, i) in label_to_id.items()}

        # Normalize
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y,
            test_size=test_size,
            random_state=random_state,
            stratify=y if len(np.unique(y)) > 1 else None
        )

        # RandomForest
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            max_depth=max_depth,
            class_weight=class_weight
        )
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        report = classification_report(
            y_test,
            y_pred,
            target_names=[id_to_label[i] for i in sorted(id_to_label.keys())],
            zero_division=0
        )

        # Save artifacts
        self.artifacts = TrainedArtifacts(
            scaler=scaler,
            model=model,
            feature_names=feature_keys,
            label_names=id_to_label
        )
        self._save_artifacts(self.model_path, self.artifacts)
        print(f"[AIModel] Model trained and saved to {self.model_path}")

        return {
            "accuracy": acc,
            "classification_report": report,
            "feature_importance": self._feature_importance(model, feature_keys),
            "label_mapping": id_to_label
        }

    # ----------------------------
    # INFERENCE
    # ----------------------------
    def predict_status(self, metrics: Dict[str, float]) -> Tuple[str, str]:
        if self.artifacts is None:
            raise RuntimeError("AIModel not loaded/trained yet.")

        feats = []
        for k in self.artifacts.feature_names:
            v = metrics.get(k, 0.0)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                v = 0.0
            feats.append(float(v))

        X_new = np.array([feats], dtype=float)
        X_scaled = self.artifacts.scaler.transform(X_new)
        class_id = int(self.artifacts.model.predict(X_scaled)[0])

        status_text = self.artifacts.label_names.get(class_id, "Unknown")
        reason = self._reason_from_metrics(metrics)

        return status_text, reason

    # ----------------------------
    # Helpers
    # ----------------------------
    def _save_artifacts(self, path: str, artifacts: TrainedArtifacts) -> None:
        with open(path, "wb") as f:
            pickle.dump(artifacts, f)

    def _load_artifacts(self, path: str) -> TrainedArtifacts:
        with open(path, "rb") as f:
            return pickle.load(f)

    def _feature_importance(self, model: RandomForestClassifier, feature_keys: List[str]) -> Dict[str, float]:
        imp = model.feature_importances_
        return {feature_keys[i]: float(imp[i]) for i in range(len(feature_keys))}

    def _reason_from_metrics(self, m: Dict[str, float]) -> str:
        """
        Human-readable reason string for dashboard.
        """
        used_mem = m.get("used_memory")
        used_sto = m.get("used_storage")
        cpu = m.get("cpuusage")
        temp = m.get("temperature")

        # Sensor glitches
        if temp is not None and (temp < -10 or temp > 120):
            return "Temperature sensor out-of-range (possible sensor glitch)"
        if cpu is not None and (cpu < 0 or cpu > 100):
            return "CPU usage out-of-range (possible metric glitch)"

        # Critical conditions
        if temp is not None and temp > 80:
            return "High temperature detected"
        if temp is not None and temp < 5:
            return "Extremely low temperature detected"
        if cpu is not None and cpu > 90:
            return "CPU usage exceeds threshold"
        if used_mem is not None and used_mem > 1600:
            return "High memory consumption detected"
        if used_sto is not None and used_sto > 3900:
            return "Storage almost full"

        # Warning conditions
        if temp is not None and 65 <= temp <= 80:
            return "Elevated temperature"
        if temp is not None and 5 <= temp < 10:
            return "Low temperature (near limit)"
        if cpu is not None and 60 <= cpu <= 90:
            return "Elevated CPU usage"
        if used_mem is not None and 1350 <= used_mem <= 1600:
            return "Elevated memory consumption"
        if used_sto is not None and 3400 <= used_sto <= 3900:
            return "Elevated storage consumption"

        return "Within normal operating range"

