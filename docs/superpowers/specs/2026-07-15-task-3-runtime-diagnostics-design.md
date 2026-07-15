# Task 3 Runtime Diagnostics Design

## Goal

Make a Task 3 timeout diagnosable from the task runner's terminal output, then
use one ROS Noetic/Gazebo reproduction to select a single corrective branch.
This change does not tune navigation parameters, move waypoints, or change the
world geometry.

## Current Evidence

- The ordered task runner has completed Task 1 and Task 2 once.
- Task 3 times out at `long_counter_left` after 90 seconds.
- The earlier GlobalPlanner `NO PATH!` failure is no longer present with
  `use_grid_path: false`.
- On timeout, the runner currently reports only the duration. It cannot show
  whether the robot is stuck near the hospital-B exit, near the service point,
  or blocked by dynamic local-costmap observations.

## Scope

Modify `src/service_robot_navigation/scripts/run_task_tests.py` only to emit
failure evidence for a waypoint that times out or reaches a non-success action
state. The existing task order, timeout, costmap-clearing behavior, and
fail-fast behavior remain unchanged.

Add offline unit tests for every new pure-Python formatting/calculation helper.
The ROS/Gazebo reproduction and its captured output are runtime verification,
not a source-code change in this task.

## Runner Behavior

For each unsuccessful waypoint result, include a `diagnostics` object when the
information can be obtained:

| Field | Source | Purpose |
| --- | --- | --- |
| `current_pose` | latest `/amcl_pose` | Locate the robot at failure. |
| `target_pose` | waypoint configuration | Preserve the intended goal. |
| `error` | existing pose-error calculation | Separate position from yaw convergence. |
| `action_state` | `SimpleActionClient.get_state()` | Distinguish timeout from terminal action failure. |
| `pose_error_message` | failed AMCL read, if any | Preserve missing-pose evidence without hiding the original failure. |

The runner will obtain a fresh pose after a timeout, after cancelling the goal.
If this read fails, it still returns the original timeout result and adds the
exception text as diagnostic evidence. It must not turn a navigation timeout
into an uncaught runner error.

The console summary will print diagnostic fields for failed waypoints in a
single readable line. Successful and already-satisfied waypoint output remains
compact.

## Runtime Procedure

In Ubuntu 20.04 with ROS Noetic, run the ordered task runner unchanged. During
Task 3, capture `/amcl_pose`, `/move_base/status`, `/cmd_vel`, and
`/move_base/DWAPlannerROS/local_plan`; in RViz display the global and local
costmaps, global plan, and DWA local plan. Retain terminal logs from the ten
seconds preceding any costmap recovery.

## Decision Rules

1. If the final pose is near the `B_left`/`B_bottom` opening and the local plan
   is absent or repeatedly rejected, widen that opening in `indoor.world`,
   regenerate `indoor.pgm` and `indoor.yaml`, then retest.
2. If the final pose is near `long_counter_left` but the reported XY or yaw
   error remains above tolerance, inspect that waypoint's orientation and the
   relevant DWA goal tolerances before changing geometry.
3. If the static global route is open but the local costmap contains an
   observation absent from the map, inspect the laser marking and clearing
   behavior before changing either geometry or planner tolerances.

No branch permits increasing the timeout merely to mask a non-convergent goal.

## Validation

Before runtime reproduction:

1. Run `python -m unittest discover -s tests -v` from the repository root.
2. Run `git diff --check`.

After runtime reproduction, the result must include the failed waypoint's
final pose (or explicit pose-read failure), goal error when available, action
state, and the four requested ROS/RViz observations. Only then may the next
change target world geometry, goal configuration, or costmap behavior.

## Non-Goals

- Re-enable `use_grid_path`.
- Retune DWA or costmap parameters without new evidence.
- Change `task_tests.yaml` waypoint positions or tolerances.
- Modify `indoor.world` or regenerate the map in this diagnostic change.
