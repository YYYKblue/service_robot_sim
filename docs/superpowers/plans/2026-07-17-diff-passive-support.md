# Differential-drive hidden passive support implementation plan

> **For Codex:** Execute this plan in the existing isolated worktree `D:\service_robot\.worktrees\diff-passive-support` on branch `codex/diff-passive-support`.

**Goal:** Stabilize the differential-drive chassis against front/back pitch in Gazebo while preserving its visible parity with the omnidirectional robot.

**Architecture:** Add two non-visual, fixed, low-friction spherical contact supports below `base_link`, located symmetrically along the forward (`x`) axis. Their contact plane matches the drive wheels' contact plane; the drive geometry, lidar, plugins, and navigation configuration remain unchanged.

**Tech Stack:** ROS Noetic URDF/Gazebo XML, Python `unittest`, `xml.etree.ElementTree`

---

### Task 1: Lock the physical-stability contract with a failing test

**Files:**
- Modify: `tests/test_diff_navigation_config.py`

**Steps:**
1. Add `test_diff_model_has_hidden_symmetric_low_friction_pitch_supports` to `DifferentialNavigationContractTest`.
2. Require the links `front_passive_support_link` and `rear_passive_support_link`, with no `visual` element.
3. Require a fixed joint to `base_link` at `(0.1800, 0, 0.0250)` and `(-0.1800, 0, 0.0250)` respectively.
4. Require each link to expose `support_collision` as a sphere of radius `0.0250`, plus a Gazebo reference block with `mu1=mu2=0.02`.
5. Run `python -m unittest discover -s tests -p test_diff_navigation_config.py -v` and confirm it fails because the supports do not exist.

### Task 2: Implement hidden, low-friction supports

**Files:**
- Modify: `src/sweeper_robot_diff2_submit_ros/urdf/sweeper_robot_diff2_submit.urdf`

**Steps:**
1. Add front and rear support links, each with a small valid inertial element and a sphere collision only—no visual geometry.
2. Attach the links to `base_link` with fixed joints at the positions required by Task 1.
3. Add Gazebo friction blocks for both support links with `mu1` and `mu2` equal to `0.02`; retain normal contact stiffness/damping consistent with the drive-wheel blocks.
4. Do not change existing body, lidar, drive wheel, plugin, or navigation configuration entries.
5. Rerun the focused test command and confirm it passes.

### Task 3: Regression verification and handoff

**Files:**
- Verify: `tests/test_diff_navigation_config.py`
- Verify: `src/sweeper_robot_diff2_submit_ros/urdf/sweeper_robot_diff2_submit.urdf`

**Steps:**
1. Parse the URDF through the full static test suite: `python -m unittest discover -s tests -v`.
2. Inspect `git diff --check` and `git diff --stat` to confirm the scope is limited to the support design, test, and URDF.
3. Commit the tested change on `codex/diff-passive-support`; do not push or merge until the user asks.
4. Tell the user the exact Ubuntu runtime checks remaining: static level posture, start/stop pitch, and five-task navigation.
