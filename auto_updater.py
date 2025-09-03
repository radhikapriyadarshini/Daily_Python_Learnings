#!/usr/bin/env python3
"""
Auto-Update System for Daily Python Learnings
Automatically updates README.md and skills-tracker.html when new entries are added
"""

import re
import json
from datetime import datetime
from pathlib import Path

class DailyLearningUpdater:
    def __init__(self, base_path="."):
        self.base_path = Path(base_path)
        self.readme_path = self.base_path / "README.md"
        self.tracker_path = self.base_path / "skills-tracker.html"
        
        # Skill categories mapping
        self.skill_categories = {
            "fundamentals": "⚡ Fundamentals",
            "circuits": "🔌 Circuit Analysis", 
            "systems": "⚙️ Power Systems",
            "analysis": "📊 System Analysis",
            "advanced": "🚀 Advanced Topics"
        }
        
        # Emoji mapping for categories
        self.category_emojis = {
            "fundamentals": "⚡",
            "circuits": "🔌",
            "systems": "⚙️", 
            "analysis": "📊",
            "advanced": "🚀"
        }
    
    def add_new_entry(self, day, title, description, category, skills_gained=None):
        """
        Add a new daily entry and update both README and tracker
        
        Args:
            day (int): Day number
            title (str): Project title
            description (str): Brief description
            category (str): Category key (fundamentals, circuits, systems, analysis, advanced)
            skills_gained (list): Optional list of specific skills gained
        """
        
        # Validate inputs
        if category not in self.skill_categories:
            raise ValueError(f"Invalid category. Must be one of: {list(self.skill_categories.keys())}")
        
        entry_data = {
            "day": day,
            "title": title,
            "description": description,
            "category": category,
            "skills_gained": skills_gained or [],
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Update README
        self.update_readme(entry_data)
        
        # Update Skills Tracker HTML
        self.update_tracker(entry_data)
        
        print(f"✅ Successfully added Day {day}: {title}")
        print(f"📝 Updated README.md and skills-tracker.html")
        
        return entry_data
    
    def update_readme(self, entry_data):
        """Update the README.md file with new entry"""
        
        if not self.readme_path.exists():
            print("❌ README.md not found!")
            return
        
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the table section
        table_pattern = r'(\| Day \| Title \| Brief Description \| Skills Covered \|\n\|---\|---\|---\|---\|)(.*?)(\n\n## )'
        
        match = re.search(table_pattern, content, re.DOTALL)
        if not match:
            print("❌ Could not find table section in README")
            return
        
        table_start = match.group(1)
        existing_entries = match.group(2)
        after_table = match.group(3)
        
        # Create new entry row
        category_display = self.skill_categories[entry_data["category"]]
        new_row = f"\n| {entry_data['day']:02d} | {entry_data['title']} | {entry_data['description']} | {category_display} |"
        
        # Update consecutive days count
        consecutive_pattern = r'- 🏆 \*\*(\d+) consecutive days\*\* of coding'
        content = re.sub(consecutive_pattern, f'- 🏆 **{entry_data["day"]} consecutive days** of coding', content)
        
        # Update total projects count (assume day = projects for now)
        projects_pattern = r'- 🎯 \*\*(\d+)\+ power system concepts\*\* implemented from scratch'
        content = re.sub(projects_pattern, f'- 🎯 **{entry_data["day"]}+ power system concepts** implemented from scratch', content)
        
        # Reconstruct the content
        before_table = content[:match.start()]
        after_match = content[match.end():]
        
        new_content = before_table + table_start + existing_entries + new_row + after_table
        
        # Write back to file
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def update_tracker(self, entry_data):
        """Update the skills-tracker.html file with new entry"""
        
        if not self.tracker_path.exists():
            print("❌ skills-tracker.html not found!")
            return
        
        with open(self.tracker_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update the dailyEntries array in JavaScript
        entries_pattern = r'let dailyEntries = \[(.*?)\];'
        
        match = re.search(entries_pattern, content, re.DOTALL)
        if not match:
            print("❌ Could not find dailyEntries array in HTML")
            return
        
        # Parse existing entries to find the right format
        existing_entries = match.group(1)
        
        # Create new entry
        new_entry = f'''            {{day: {entry_data["day"]}, title: "{entry_data["title"]}", description: "{entry_data["description"]}", skills: ["{entry_data["category"]}"], date: "{entry_data["date"]}"}}'''
        
        # Add to existing entries
        updated_entries = existing_entries.rstrip() + ',\n' + new_entry
        
        # Replace in content
        new_content = content.replace(match.group(0), f'let dailyEntries = [{updated_entries}\n        ];')
        
        # Update stats
        new_content = re.sub(r'totalDays: \d+', f'totalDays: {entry_data["day"]}', new_content)
        
        # Update stat displays
        new_content = re.sub(
            r'<div class="stat-value" id="totalDays">\d+</div>',
            f'<div class="stat-value" id="totalDays">{entry_data["day"]}</div>',
            new_content
        )
        
        new_content = re.sub(
            r'<div class="stat-value" id="projectsCompleted">\d+</div>',
            f'<div class="stat-value" id="projectsCompleted">{entry_data["day"]}</div>',
            new_content
        )
        
        # Write back to file
        with open(self.tracker_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def get_next_day_number(self):
        """Get the next day number by reading current README"""
        if not self.readme_path.exists():
            return 1
        
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find highest day number
        day_pattern = r'\| (\d+) \|'
        days = re.findall(day_pattern, content)
        
        if days:
            return max(int(day) for day in days) + 1
        return 1
    
    def interactive_add(self):
        """Interactive mode to add new entries"""
        print("🚀 Daily Python Learning Entry Creator")
        print("=" * 40)
        
        # Get next day number
        next_day = self.get_next_day_number()
        print(f"📅 Adding entry for Day {next_day}")
        
        # Get user inputs
        title = input("📝 Project Title: ").strip()
        description = input("📄 Brief Description: ").strip()
        
        print("\n📚 Available Categories:")
        for i, (key, display) in enumerate(self.skill_categories.items(), 1):
            print(f"  {i}. {key} - {display}")
        
        while True:
            try:
                cat_choice = int(input("\n🎯 Select category (1-5): ")) - 1
                category_keys = list(self.skill_categories.keys())
                if 0 <= cat_choice < len(category_keys):
                    category = category_keys[cat_choice]
                    break
                else:
                    print("❌ Invalid choice. Please select 1-5.")
            except ValueError:
                print("❌ Please enter a number.")
        
        # Optional skills
        skills_input = input("\n🛠️  Specific skills gained (comma-separated, optional): ").strip()
        skills_gained = [s.strip() for s in skills_input.split(",")] if skills_input else []
        
        # Confirm before adding
        print(f"\n📋 Summary:")
        print(f"   Day: {next_day}")
        print(f"   Title: {title}")
        print(f"   Description: {description}")
        print(f"   Category: {self.skill_categories[category]}")
        if skills_gained:
            print(f"   Skills: {', '.join(skills_gained)}")
        
        confirm = input("\n✅ Add this entry? (y/n): ").lower().strip()
        
        if confirm == 'y':
            try:
                self.add_new_entry(next_day, title, description, category, skills_gained)
                print(f"\n🎉 Successfully added Day {next_day}!")
                print("📁 Files updated:")
                print(f"   - {self.readme_path}")
                print(f"   - {self.tracker_path}")
            except Exception as e:
                print(f"❌ Error adding entry: {e}")
        else:
            print("❌ Entry cancelled.")


def main():
    """Main function for command line usage"""
    import sys
    
    updater = DailyLearningUpdater()
    
    if len(sys.argv) == 1:
        # Interactive mode
        updater.interactive_add()
    elif len(sys.argv) >= 4:
        # Command line mode
        try:
            day = int(sys.argv[1]) if sys.argv[1] != 'auto' else updater.get_next_day_number()
            title = sys.argv[2]
            description = sys.argv[3]
            category = sys.argv[4] if len(sys.argv) > 4 else 'analysis'
            
            updater.add_new_entry(day, title, description, category)
        except (ValueError, IndexError) as e:
            print(f"❌ Error: {e}")
            print("Usage: python auto_updater.py [day|auto] 'title' 'description' [category]")
            print("Or run without arguments for interactive mode")
    else:
        print("Usage:")
        print("  Interactive mode: python auto_updater.py")
        print("  Command line: python auto_updater.py [day|auto] 'title' 'description' [category]")
        print(f"  Categories: {', '.join(updater.skill_categories.keys())}")


if __name__ == "__main__":
    main()
