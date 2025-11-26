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


class AIModel(BaseService):
    """
    AI model service skeleton:
    - load/receive data
    - preprocess/normalize
    - split train/test
    - train RandomForest
    - evaluate (accuracy, classification report)
    - save/load artifacts (scaler + model)
    - predict on new samples

    Follows the docs steps:
    prepare data → clean/split → train RF →
    evaluate (accuracy/precision/recall/F1) →
    feature importance → deploy (save .pkl)

    Empty AI model service skeleton.
    """
    
    def __init__(self, model_path: str = "model.pkl"):
        super().__init__("AIModel")
        self.model_path = model_path

    def start(self) -> None:
        super().start()
        # TODO: load AI model resources

    def stop(self) -> None:
        # TODO: release AI model resources
        super().stop()

    # -----------------------------------------------------------------
    # Training
    # -----------------------------------------------------------------

    def train(self, rows: list[Dict[str, any]], feature_keys: list[str], label_key: str) -> None:
        """
        Train the AI model from given data rows.
        :param rows: List of data rows (dicts)
        :param feature_keys: List of keys to use as features
        :param label_key: Key to use as label
        """
        pass  # TODO: implement training logic

        x : list = [] # ML features as float
        y : list = [] # ML Labels to int 0, 1, 2
        label_to_id : Dict[str, int] = {}
        next_id : int = 0

        for row in rows:
            for k in feature_keys:
                key : float = row.get(k,0.0) # return 0.0 if key not found
                x.append(key) # Extract each value from dicts

                label : str = row.get(label_key, "Healthy")
                if label not in label_to_id:
                    label_to_id[label] = next_id
                    next_id += 1
                    y.append(label_to_id[label])

        x = np.array(x, dtype = float)
        y = np.array(y, dtype = int)
