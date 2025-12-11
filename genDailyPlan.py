import os
import re
import random
import sys
from datetime import datetime

DOCS_DIR = "docs"

def scan_files():
    """
    Scans the docs directory recursively.
    Returns a dictionary: { subDirNameString: { problemName: [] } }
    """
    result_dict = {}
    if not os.path.exists(DOCS_DIR):
        return result_dict
    
    for root, dirs, files in os.walk(DOCS_DIR):
        # Get relative path from docs dir to use as category/folder name
        rel_path = os.path.relpath(root, DOCS_DIR)
        
        if rel_path == ".":
            continue
            
        sub_dict = {}
        for filename in files:
            if filename.endswith(".md"):
                # Use filename without extension as key to match index.md
                name = os.path.splitext(filename)[0]
                sub_dict[name] = []
        
        if sub_dict:
            result_dict[rel_path] = sub_dict
                    
    return result_dict

def parse_index_file(scanned_data):
    """
    Parses docs/index.md to extract review progress and updates scanned_data.
    scanned_data: { subDirName: { problemName: [] } }
    Returns: Updated scanned_data with [weight, date1, date2, ...] for found entries.
    """
    index_path = os.path.join(DOCS_DIR, "index.md")
    if not os.path.exists(index_path):
        return scanned_data

    with open(index_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_subdir = None
    in_review_section = False
    processing_table = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("## Reviewing Timeline"):
            in_review_section = True
            continue
        
        if not in_review_section:
            continue
            
        if line.startswith("## ") and not line.startswith("## Reviewing Timeline"):
            # Left the section
            break
            
        if line.startswith("### "):
            current_subdir = line.replace("### ", "").strip()
            # Ignore "最新更新" section for table parsing
            if current_subdir.startswith("最新更新"):
                current_subdir = None
            processing_table = False
            continue
            
        if ":---" in line:
            processing_table = True
            continue
            
        if processing_table and line.startswith("|"):
            parts = [p.strip() for p in line.split('|')]
            # Remove empty start/end if they exist due to leading/trailing pipes
            if len(parts) > 0 and parts[0] == '': parts.pop(0)
            if len(parts) > 0 and parts[-1] == '': parts.pop(-1)
            
            if len(parts) >= 2 and current_subdir:
                raw_name = parts[0]
                # Handle markdown link [name](url)
                match = re.match(r"\[(.*?)\]\(.*?\)", raw_name)
                if match:
                    problem_name = match.group(1)
                else:
                    problem_name = raw_name
                
                # Only update if it exists in scanned_data (file exists)
                if current_subdir in scanned_data and problem_name in scanned_data[current_subdir]:
                    try:
                        weight = int(parts[1])
                    except ValueError:
                        weight = 0
                    
                    dates = [d for d in parts[2:] if d]
                    
                    scanned_data[current_subdir][problem_name] = [weight] + dates
        elif processing_table and line == "":
             processing_table = False

    return scanned_data

def select_problems(data):
    """
    Selects problems to review based on mastery level.
    Returns a list of (subdir, problem_name) tuples.
    """
    candidates = []
    weights = []
    
    for subdir, problems in data.items():
        for name, info in problems.items():
            # info is [weight, date1, date2, ...] or []
            mastery = info[0] if info else 0
            
            candidates.append((subdir, name))
            # Lower mastery = higher probability. 
            # Using exponential decay: 2^(-mastery)
            # Mastery 0 -> 1
            # Mastery 1 -> 0.5
            # Mastery -1 -> 2
            weights.append(2.0 ** (-mastery))
            
    if not candidates:
        return []

    # Determine count: min(half of total, 8)
    # Ensure at least 1 if candidates exist
    count = max(1, min(len(candidates) // 2, 8))
        
    # Normalize weights
    total_weight = sum(weights)
    if total_weight == 0:
        probs = [1.0/len(weights)] * len(weights)
    else:
        probs = [w / total_weight for w in weights]
        
    # Select unique problems
    # random.choices returns list with replacement, so we oversample and dedup
    selected = []
    seen = set()
    
    # Safety check if we have fewer candidates than requested count
    if len(candidates) <= count:
        return candidates

    # Try to select unique items
    while len(selected) < count:
        # Select one at a time to ensure uniqueness check works
        choice = random.choices(candidates, weights=probs, k=1)[0]
        if choice not in seen:
            seen.add(choice)
            selected.append(choice)
            
    return selected

def parse_existing_today_section(lines):
    """
    Parses the '### 最新更新: ...' section.
    Returns: (date_str, existing_new_problems, existing_review_problems)
    existing_new_problems: list of (subdir, name)
    existing_review_problems: list of (subdir, name)
    """
    date_str = None
    existing_new = []
    existing_review = []
    
    start_index = -1
    end_index = -1
    
    # Find section range
    for i, line in enumerate(lines):
        if line.strip().startswith("### 最新更新:"):
            start_index = i
            date_str = line.strip().replace("### 最新更新:", "").strip()
            break
            
    if start_index == -1:
        return None, [], []
        
    # Find end
    for i in range(start_index + 1, len(lines)):
        if lines[i].strip().startswith("## "): # Next main section
            end_index = i
            break
    if end_index == -1:
        end_index = len(lines)
        
    section_lines = lines[start_index:end_index]
    
    current_list = None
    for line in section_lines:
        line = line.strip()
        if line == "#### 新题":
            current_list = existing_new
        elif line == "#### 复习":
            current_list = existing_review
        elif line.startswith("- ["):
            # Parse - [name](subdir/name.md)
            match = re.match(r"- \[(.*?)\]\((.*?)\)", line)
            if match and current_list is not None:
                path = match.group(2)
                if "/" in path:
                    parts = path.split("/")
                    # parts[-1] is filename.md, parts[-2] is subdir
                    if len(parts) >= 2:
                        subdir = parts[-2]
                        name = os.path.splitext(parts[-1])[0]
                        current_list.append((subdir, name))
                        
    return date_str, existing_new, existing_review

def update_index_file(data, selected_problems, new_problems, update_only=False):
    """
    Updates the data with new review info and rewrites the Reviewing Timeline section in index.md.
    Also updates the ### Today: section.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Update data in memory
    for subdir, name in selected_problems:
        info = data[subdir][name]
        if not info:
            # Initialize if empty
            info = [0]
        
        # Increment mastery
        info[0] += 1
        # Add today's date
        info.insert(1, today_str)
        # Keep only last 3 dates (so mastery + 3 dates = 4 elements max? 
        # User said "最近3次复习日期", so list length should be 1 (weight) + 3 (dates) = 4
        if len(info) > 4:
            info = info[:4]
        
        data[subdir][name] = info

    # 2. Rewrite index.md
    index_path = os.path.join(DOCS_DIR, "index.md")
    if not os.path.exists(index_path):
        lines = []
    else:
        with open(index_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
    # Parse existing section to support incremental updates
    last_date, existing_new, existing_review = parse_existing_today_section(lines)
    
    is_same_day = (last_date == today_str)
    
    final_new_problems = []
    final_review_problems = []
    
    if is_same_day:
        # Merge new problems: existing + current (deduplicated)
        seen = set()
        for item in existing_new:
            final_new_problems.append(item)
            seen.add(item)
        for item in new_problems:
            if item not in seen:
                final_new_problems.append(item)
                seen.add(item)
                
        if update_only:
            # Keep existing review problems if we are just updating file list
            final_review_problems = existing_review
        else:
            # Overwrite review problems with newly selected ones if generating plan
            final_review_problems = selected_problems
    else:
        # Different day or first run: use current findings
        final_new_problems = new_problems
        final_review_problems = selected_problems

    # Find start of Reviewing Timeline
    cut_index = len(lines)
    for i, line in enumerate(lines):
        if line.strip() == "## Reviewing Timeline":
            cut_index = i
            break
            
    new_content = lines[:cut_index]
    
    # Update ### 最新更新: section
    today_index = -1
    for i, line in enumerate(new_content):
        if line.strip().startswith("### 最新更新:"):
            today_index = i
            break
    
    today_lines = [f"### 最新更新: {today_str}\n\n"]

    if final_new_problems:
        today_lines.append("#### 新题\n")
        for subdir, name in final_new_problems:
                link = f"{subdir}/{name}.md"
                today_lines.append(f"- [{name}]({link})\n")
        today_lines.append("\n")

    if not update_only or (update_only and is_same_day and final_review_problems):
        today_lines.append("#### 复习\n")
        if final_review_problems:
            for subdir, name in final_review_problems:
                link = f"{subdir}/{name}.md"
                today_lines.append(f"- [{name}]({link})\n")
        else:
            today_lines.append("今日无复习计划。\n")
        today_lines.append("\n")
    elif not final_new_problems:
        # If update only and no new problems, we can say so or leave it empty
        today_lines.append("无新题。\n\n")
    
    if today_index != -1:
        # Find end of section
        end_index = len(new_content)
        for i in range(today_index + 1, len(new_content)):
            line = new_content[i].strip()
            # Stop at next header of level 1, 2, or 3.
            # We want to include #### headers in the replacement range so they get overwritten.
            if line.startswith("#") and not line.startswith("####"):
                end_index = i
                break
        new_content[today_index:end_index] = today_lines # Replace including the header
    else:
        # Append if not found
        new_content.extend(today_lines)
    
    # Ensure there is a newline before the section if file is not empty
    if new_content and not new_content[-1].endswith('\n'):
        new_content.append('\n')
        
    new_content.append("## Reviewing Timeline\n")
    
    # Generate tables for each subdir
    for subdir in sorted(data.keys()):
        new_content.append(f"\n### {subdir}\n\n")
        new_content.append("| 习题 | 掌握权重 | 上次复习 | 上上次复习 | 上上上次复习 |\n")
        new_content.append("| :--- | :---: | :--- | :--- | :--- |\n")
        
        problems = data[subdir]
        for name in sorted(problems.keys()):
            info = problems[name]
            if not info:
                weight = 0
                dates = []
            else:
                weight = info[0]
                dates = info[1:]
                
            dates_str = " | ".join(dates)
            # Pad pipes if fewer dates
            pipe_padding = " | " * (3 - len(dates))
            
            name_with_link = f"[{name}]({subdir}/{name}.md)"
            line = f"| {name_with_link} | {weight} | {dates_str}{pipe_padding} |\n"
            new_content.append(line)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

def main():
    update_only = "-u" in sys.argv
    print("--- Algorithm Review Manager ---")
    
    # 1. Scan files
    data = scan_files()
    print(f"Scanned {sum(len(v) for v in data.values())} problems.")
    
    # 2. Parse existing progress
    data = parse_index_file(data)
    
    # Identify new problems (empty info)
    new_problems = []
    for subdir, problems in data.items():
        for name, info in problems.items():
            if not info:
                new_problems.append((subdir, name))
    
    selected = []
    if not update_only:
        # 3. Generate Plan
        selected = select_problems(data)
        
        print("\n" + "="*30)
        print(f"📅 Review Plan for {datetime.now().strftime('%Y-%m-%d')}")
        print("="*30)
        
        if not selected:
            print("No problems found to review.")
        else:
            for subdir, name in selected:
                info = data[subdir][name]
                mastery = info[0] if info else 0
                print(f"- [ ] {subdir}/{name} (Mastery: {mastery})")
    else:
        print("\nUpdate only mode: Syncing file list.")
        if new_problems:
            print(f"Found {len(new_problems)} new problems.")
            for subdir, name in new_problems:
                print(f"- {subdir}/{name}")

    # 4. Update index.md
    update_index_file(data, selected, new_problems, update_only)
    
    if update_only:
        print("\nUpdated index.md (synced file list).")
    elif selected:
        print("\nUpdated index.md with new review dates and mastery levels.")

if __name__ == "__main__":
    main()
