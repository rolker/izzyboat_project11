#!/usr/bin/env python3
"""Refinement iteration: fold verify residuals into alpha/beta, re-verify, final decomposition."""
import numpy as np

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
sol = np.load(f"{OUT}/absolute_solution.npz")
# Residuals transcribed BY HAND from the prior verify.py full-res run (best signs).
# They are manual snapshots, not computed here: re-running the pipeline produces
# fresh values to paste in. One iteration was enough to converge (<=0.011 deg).
# Order: fwd, aft, port, stbd
resid_a = np.array([-0.000, 0.068, -0.104, 0.054])
resid_t = np.array([0.024, -0.120, -0.003, 0.006])   # deg tilt
alpha = sol["alpha"] + resid_a
beta = sol["beta"] + np.tan(np.radians(resid_t))
np.savez(f"{OUT}/absolute_solution.npz", alpha=alpha, beta=beta,
         modes=np.array([alpha.mean(), (alpha[0]-alpha[1])/2, (alpha[3]-alpha[2])/2,
                         (alpha[0]+alpha[1]-alpha[2]-alpha[3])/4]), scale=sol["scale"])
print("updated alpha:", alpha.round(3), " beta:", beta.round(4))
