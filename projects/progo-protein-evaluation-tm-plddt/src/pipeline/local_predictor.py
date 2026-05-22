# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
LOCAL AXONOS MODIFICATION - No API Key
Local structure prediction for AxonOS (8x V100) without NVIDIA cloud services.
"""

import os
from typing import Dict

try:
    import torch

    CUDA_AVAILABLE = torch.cuda.is_available()
    if CUDA_AVAILABLE:
        CUDA_DEVICE_COUNT = torch.cuda.device_count()
    else:
        CUDA_DEVICE_COUNT = 0
except ImportError:
    CUDA_AVAILABLE = False
    CUDA_DEVICE_COUNT = 0


def predict_structure_local(sequence: str, output_dir: str = "output/temp") -> dict:
    """Local placeholder structure predictor for AxonOS (no API key)."""
    os.makedirs(output_dir, exist_ok=True)
    pdb_path = os.path.join(output_dir, f"local_{hash(sequence[:50])}.pdb")

    # LOCAL AXONOS MODIFICATION - No API Key
    if CUDA_AVAILABLE:
        device_name = torch.cuda.get_device_name(0)
        gpu_remark = f"GPU: {device_name} ({CUDA_DEVICE_COUNT} device(s) available)"
    else:
        gpu_remark = "GPU: not available (CPU fallback)"

    # Simulate realistic pLDDT scores
    plddt = [round(65 + (i % 35), 2) for i in range(len(sequence))]

    # Generate placeholder PDB with per-residue pLDDT in B-factor column
    pdb_lines = [
        "REMARK   Local AxonOS placeholder structure",
        "REMARK   Generated for testing - No NVIDIA API used",
        f"REMARK   {gpu_remark}",
    ]
    for i, score in enumerate(plddt, start=1):
        x = 10.0 + (i % 10) * 3.8
        y = 10.0 + (i // 10) * 3.8
        z = 10.0
        pdb_lines.append(
            f"ATOM  {i:5d}  CA  GLY A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00{score:6.2f}"
        )
    pdb_lines.append("TER")
    pdb_lines.append("END")
    dummy_pdb = "\n".join(pdb_lines) + "\n"

    with open(pdb_path, "w") as f:
        f.write(dummy_pdb)

    return {
        "pdb_path": pdb_path,
        "plddt": plddt,
        "mean_plddt": sum(plddt) / len(plddt) if plddt else 0.0,
        "sequence_length": len(sequence),
    }
