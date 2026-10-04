"""Print the complete synthetic four-case geometric record; no experiments."""
import csv
import math
import sys

FIELDS = [
    "case_id", "provenance", "support_state", "groove_x_mm", "panel_angle_deg",
    "P_x_mm", "P_z_mm", "Q_x_mm", "Q_z_mm", "T_x_mm", "T_z_mm",
    "P_Q_distance_mm", "active_foot_groove_contacts", "permanent_revolute_joints",
    "physical_experiments",
]


def records():
    for index, d in enumerate((50.0, 75.0, 100.0), start=1):
        cosine = (60.0**2 + d**2 - 70.0**2) / (2.0 * 60.0 * d)
        theta = math.acos(cosine)
        px, pz = 60.0 * cosine, 60.0 * math.sin(theta)
        numeric = [d, math.degrees(theta), px, pz, d, 0.0, 2.0 * px,
                   2.0 * pz, math.hypot(d - px, pz)]
        yield [f"S{index}", "synthetic_analytic", "seated"] + [
            f"{value:.6f}" for value in numeric
        ] + [1, 2, 0]
    qx, qz = 70.0 * math.cos(math.radians(30.0)), 25.0
    numeric = [90.0, 0.0, 60.0, qx, qz, 0.0, 120.0,
               math.hypot(qx, qz - 60.0)]
    yield ["R", "synthetic_analytic", "released_externally_held", "NA"] + [
        f"{value:.6f}" for value in numeric
    ] + [0, 2, 0]


if __name__ == "__main__":
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(records())
