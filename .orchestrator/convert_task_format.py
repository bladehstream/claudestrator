#!/usr/bin/env python3
"""Convert task_queue.md from BOLD to hybrid TABLE+BOLD format.

Converts metadata fields (Priority, Status, Category, Depends On) to TABLE format.
Preserves prose fields (Description, Steps, Expected Result) in BOLD format.
Adds --- separator between metadata table and prose section.
"""

import re

def convert_task_queue(input_path: str):
    """Convert task_queue.md to hybrid format."""
    with open(input_path, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    result = []
    i = 0

    # Metadata fields to convert to TABLE
    metadata_fields = {'Priority', 'Status', 'Category', 'Depends On'}
    # Prose fields to keep as BOLD
    prose_fields = {'Description', 'Steps', 'Expected Result'}

    while i < len(lines):
        line = lines[i]

        # Check if this is a task header (### BUILD or #### TEST)
        if re.match(r'^#{3,4}\s+(BUILD|TEST)', line):
            result.append(line)
            i += 1

            # Collect metadata and prose
            metadata = {}
            prose_lines = []
            in_steps = False

            while i < len(lines):
                current = lines[i]

                # Next task header - stop collecting
                if re.match(r'^#{3,4}\s+(BUILD|TEST)', current):
                    break

                # Section header (## BUILD Tasks, ## TEST Tasks, etc.)
                if re.match(r'^##\s+', current):
                    break

                # Empty line between tasks
                if current.strip() == '' and not in_steps:
                    i += 1
                    break

                # Check for BOLD field
                match = re.match(r'^\*\*(\w+(?:\s+\w+)?):\*\*\s*(.*)$', current)
                if match:
                    field, value = match.groups()
                    if field in metadata_fields:
                        metadata[field] = value
                        i += 1
                        continue
                    elif field in prose_fields:
                        prose_lines.append(current)
                        in_steps = (field == 'Steps')
                        i += 1
                        continue

                # Numbered step line (part of Steps)
                if in_steps and re.match(r'^\d+\.', current):
                    prose_lines.append(current)
                    i += 1
                    continue

                # Any other line
                if in_steps:
                    in_steps = False

                i += 1

            # Write metadata table
            if metadata:
                result.append('')
                result.append('| Field | Value |')
                result.append('|-------|-------|')
                for field in ['Priority', 'Status', 'Category', 'Depends On']:
                    if field in metadata:
                        result.append(f'| {field} | {metadata[field]} |')
                result.append('')
                result.append('---')
                result.append('')

            # Write prose lines
            result.extend(prose_lines)
            result.append('')

        else:
            result.append(line)
            i += 1

    # Write output
    output = '\n'.join(result)
    # Clean up multiple blank lines
    output = re.sub(r'\n{3,}', '\n\n', output)

    with open(input_path, 'w') as f:
        f.write(output)

    return output

def verify_conversion(content: str):
    """Verify the conversion was successful."""
    # Count patterns
    table_pending = len(re.findall(r'\| Status \| pending \|', content))
    table_completed = len(re.findall(r'\| Status \| completed \|', content))
    bold_status = len(re.findall(r'\*\*Status:\*\*', content))

    print(f"Table '| Status | pending |': {table_pending}")
    print(f"Table '| Status | completed |': {table_completed}")
    print(f"Bold '**Status:**': {bold_status}")

    if bold_status == 0:
        print("\nSUCCESS: All Status fields converted to TABLE format")
        return True
    else:
        print("\nWARNING: Some BOLD Status fields remain")
        return False

def main():
    input_file = '.orchestrator/task_queue.md'

    print("Converting task_queue.md to hybrid TABLE+BOLD format...")
    print("=" * 60)

    content = convert_task_queue(input_file)

    print("\nVerification:")
    print("-" * 60)
    verify_conversion(content)

    print("\n" + "=" * 60)
    print("Conversion complete!")

if __name__ == '__main__':
    main()
