"""
Spatial Validation and Cross-Validation Module
Implements Random K-Fold and Spatial Block Cross-Validation (K-Means spatial clustering).
Prevents spatial autocorrelation leakage during model evaluation.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.cluster import KMeans

class SpatialBlockKFold:
    """
    Spatial Block Cross-Validator.
    Partitions geographical coordinates into K spatially contiguous clusters/blocks.
    Guarantees no spatial overlap between training and validation folds.
    """
    def __init__(self, n_splits: int = 5, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state
        self.cluster_labels_ = None
        
    def split(self, X, y=None, groups=None, coords=None):
        if coords is None:
            if isinstance(X, pd.DataFrame) and "latitude" in X.columns and "longitude" in X.columns:
                coords = X[["latitude", "longitude"]].values
            else:
                raise ValueError("Spatial coordinates (latitude, longitude) must be provided for SpatialBlockKFold.")
                
        # Perform K-Means clustering on geographic coordinates
        kmeans = KMeans(n_clusters=self.n_splits, random_state=self.random_state, n_init=10)
        self.cluster_labels_ = kmeans.fit_predict(coords)
        
        for fold in range(self.n_splits):
            val_idx = np.where(self.cluster_labels_ == fold)[0]
            train_idx = np.where(self.cluster_labels_ != fold)[0]
            yield train_idx, val_idx
            
    def get_n_splits(self, X=None, y=None, groups=None):
        return self.n_splits
