#!/usr/bin/env python3
"""
SubagentStop hook to ensure agents write their completion markers.

This hook runs when a subagent finishes. It checks if the agent created
its .done marker file. If not, it blocks the agent from stopping and
tells it to create the marker.
"""
import json
import sys
import os
import re

def find_task_id_in_transcript(transcript_path):
    """Extract task ID from the agent's transcript."""
    if not os.path.exists(transcript_path):
        return None

    try:
        with open(transcript_path, 'r') as f:
            content = f.read()

        # Look for TASK-XXX pattern in the transcript
        # The prompt should contain something like "TASK: TASK-001" or "TASK-001"
        matches = re.findall(r'TASK-\d+(?:-\d+)?', content)
        if matches:
            return matches[0]  # Return first match

    except Exception:
        pass

    return None

def find_expected_marker_in_transcript(transcript_path):
    """Look for the expected marker path mentioned in the prompt."""
    if not os.path.exists(transcript_path):
        return None

    try:
        with open(transcript_path, 'r') as f:
            content = f.read()

        # Look for .orchestrator/complete/*.done path in transcript
        matches = re.findall(r'[\'"]?([^\s\'"]*\.orchestrator/complete/[^\s\'"]+\.done)[\'"]?', content)
        if matches:
            return matches[0]

    except Exception:
        pass

    return None

def check_marker_written_in_transcript(transcript_path):
    """Check if a Write tool call to .done was made."""
    if not os.path.exists(transcript_path):
        return False

    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    # Look for successful Write tool calls to .done files
                    if entry.get('type') == 'tool_result':
                        # Check if it was a Write to a .done file
                        pass  # Hard to determine from result alone
                    if entry.get('type') == 'tool_use':
                        tool = entry.get('name', '')
                        if tool == 'Write':
                            input_data = entry.get('input', {})
                            file_path = input_data.get('file_path', '')
                            if '.done' in file_path and 'orchestrator/complete' in file_path:
                                return True
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return False

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if we're already in a stop hook loop (prevent infinite loops)
    if input_data.get('stop_hook_active', False):
        # Already retrying, let it stop this time
        sys.exit(0)

    transcript_path = input_data.get('transcript_path', '')
    cwd = input_data.get('cwd', os.getcwd())

    # Try to find the expected marker path from the transcript
    expected_marker = find_expected_marker_in_transcript(transcript_path)
    task_id = find_task_id_in_transcript(transcript_path)

    # If we found a marker path, check if it exists
    if expected_marker:
        # Handle both relative and absolute paths
        if expected_marker.startswith('/'):
            marker_path = expected_marker
        else:
            marker_path = os.path.join(cwd, expected_marker)

        if os.path.exists(marker_path):
            # Marker exists, allow stop
            sys.exit(0)
        else:
            # Marker missing! Block the agent and tell it to create it
            output = {
                "decision": "block",
                "reason": f"""CRITICAL: You have NOT created the completion marker file!

The orchestrator is waiting for this file: {expected_marker}

You MUST create it NOW using:
Write("{expected_marker}", "done")

Do this IMMEDIATELY. The system is blocked until this file exists."""
            }
            print(json.dumps(output))
            sys.exit(0)

    # If we found a task ID but no explicit marker path, construct it
    if task_id:
        marker_path = os.path.join(cwd, '.orchestrator', 'complete', f'{task_id}.done')

        if os.path.exists(marker_path):
            # Marker exists, allow stop
            sys.exit(0)
        else:
            # Marker missing!
            output = {
                "decision": "block",
                "reason": f"""CRITICAL: You have NOT created the completion marker file!

Your task was: {task_id}
The orchestrator is waiting for: .orchestrator/complete/{task_id}.done

You MUST create it NOW using:
Write(".orchestrator/complete/{task_id}.done", "done")

Do this IMMEDIATELY. The system is blocked until this file exists."""
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check if any Write to .done was made in the transcript
    if check_marker_written_in_transcript(transcript_path):
        # Looks like they tried to write it, allow stop
        sys.exit(0)

    # Couldn't determine task, but check if complete dir has any recent files
    agent_complete_dir = os.path.join(cwd, '.orchestrator', 'complete')
    if os.path.isdir(agent_complete_dir):
        # If there are .done files, maybe it worked
        done_files = [f for f in os.listdir(agent_complete_dir) if f.endswith('.done')]
        if done_files:
            # Some markers exist, allow stop
            sys.exit(0)

    # Can't determine if marker was created - allow stop but warn
    # (Better to not block indefinitely if we can't figure out the task)
    sys.exit(0)

if __name__ == '__main__':
    main()
