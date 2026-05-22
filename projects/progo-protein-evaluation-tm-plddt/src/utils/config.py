# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Configuration module for ProteinGO pipeline.
Handles pipeline settings for local AxonOS execution.

LOCAL AXONOS MODIFICATION - No API Key
"""

import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# LOCAL AXONOS MODIFICATION - No API Key
# NVIDIA API / NGC authentication removed; pipeline runs fully locally.
LOCAL_PREDICTION_MODE = True
logger.info("Local AxonOS prediction mode enabled (no NVIDIA API key required)")

# Directory Configuration
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"

# Ensure directories exist
for directory in [INPUT_DIR, GROUND_TRUTH_DIR, OUTPUT_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Pipeline Configuration
MAX_SEQUENCE_LENGTH = 1000  # Maximum sequence length for local prediction
BATCH_SIZE = 10  # Number of sequences to process in parallel
TIMEOUT = 300  # Local processing timeout in seconds

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def validate_config():
    """Validate the configuration settings for local AxonOS mode."""
    if not all(dir.exists() for dir in [INPUT_DIR, GROUND_TRUTH_DIR, OUTPUT_DIR, LOG_DIR]):
        raise ValueError("Required directories do not exist")

    return True
