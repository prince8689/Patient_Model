from pathlib import Path

root = Path(__file__).resolve().parent.parent.parent

lines = []
lines.append("=== Item 8: Owner Pre-push and Deployment Instructions ===")

lines.append("\n--- 1. Exact PowerShell commands to add remote and push main and tag ---")
lines.append("# Check repository status and verify remote is empty:")
lines.append("git -C d:\\Patient_Model status -sb")
lines.append("git -C d:\\Patient_Model remote -v")
lines.append("\n# Add remote and push main branch and submission tag:")
lines.append("git -C d:\\Patient_Model remote add origin https://github.com/<owner>/DiaTwin.git")
lines.append("git -C d:\\Patient_Model push -u origin main")
lines.append("git -C d:\\Patient_Model push origin submission-v1")

lines.append("\n--- 2. Command to open repository in private browsing window ---")
lines.append("Start-Process \"msedge.exe\" -ArgumentList \"-inprivate\", \"https://github.com/<owner>/DiaTwin\"")
lines.append("# Or for Google Chrome:")
lines.append("Start-Process \"chrome.exe\" -ArgumentList \"--incognito\", \"https://github.com/<owner>/DiaTwin\"")

lines.append("\n--- 3. Streamlit Community Cloud Deployment Settings ---")
lines.append("Repository:       https://github.com/<owner>/DiaTwin")
lines.append("Branch:           main")
lines.append("Main file path:   app/main.py")
lines.append("Python version:   3.12")
lines.append("Secrets (Settings -> Secrets):")
lines.append('DIATWIN_DEMO_BUNDLE = "1"')

lines.append("\n--- 4. List of README placeholders for the owner to fill ---")
lines.append("1. Line 7:  Live Demo URL:      [LIVE DEMO URL]")
lines.append("2. Line 8:  Demo Video URL:     [VIDEO URL]")
lines.append("3. Line 104: Tools/Mentors:      [TO BE FILLED BY TEAM: tools, libraries, data sources, mentors]")
lines.append("4. Line 119: Team and Contact:   [TO BE FILLED BY TEAM: Member Names, Contact Information]")

output = "\n".join(lines) + "\n"
out_path = root / "reports" / "qa" / "logs" / "item8.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(output)

print("Item 8 logged successfully.")
