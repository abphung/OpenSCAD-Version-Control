import sys
import os
import shutil
import time
import subprocess
import git
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import difflib

class DebugWindow:
    def __init__(self, root, working_dir, new_file_path, repo):
        self.root = root
        self.root.title("STL Version Control - Debug Window")
        self.root.geometry("800x600")

        self.working_dir = working_dir
        self.new_file_path = new_file_path
        self.repo = repo
        self.file_name = os.path.basename(new_file_path)

        # Labels
        tk.Label(root, text="Working Directory:").pack()
        tk.Label(root, text=working_dir, fg="blue").pack()

        tk.Label(root, text="Copied File:").pack()
        tk.Label(root, text=self.file_name, fg="blue").pack()

        # Git Diff Display
        tk.Label(root, text="Git Changes (Before & After):").pack()
        self.diff_text = scrolledtext.ScrolledText(root, height=15, width=90)
        self.diff_text.pack(pady=5)
        self.diff_output = self.load_git_diff()

        # If no changes, commit automatically and open file
        if not self.diff_output.strip():
            self.auto_commit_and_open()
            return

        # Show Before & After Changes
        tk.Label(root, text="Side-by-Side File Comparison:").pack()
        self.diff_view = scrolledtext.ScrolledText(root, height=15, width=90)
        self.diff_view.pack(pady=5)
        self.show_side_by_side_diff()

        # Commit Message Entry
        tk.Label(root, text="Commit Message:").pack()
        self.commit_entry = tk.Entry(root, width=50)
        self.commit_entry.pack(pady=5)

        # Commit Button
        self.commit_button = tk.Button(root, text="Commit & Open in Bambu Studio", command=self.commit_and_open)
        self.commit_button.pack(pady=10)

    def load_git_diff(self):
        """Load Git diff into the text box."""
        try:
            diff_output = self.repo.git.diff()  # Get unstaged changes
            if not diff_output:
                return ""  # No changes
        except Exception as e:
            diff_output = f"Error fetching git diff:\n{e}"
        
        self.diff_text.insert(tk.END, diff_output)
        return diff_output

    def show_side_by_side_diff(self):
        """Display before and after file changes side by side with highlighting."""
        try:
            repo_path = self.repo.working_dir
            rel_path = os.path.relpath(self.new_file_path, repo_path)
            
            # Get previous version from Git
            try:
                before_content = self.repo.git.show(f"HEAD:{rel_path}").splitlines()
            except:
                before_content = ["(No previous version)"]

            with open(self.new_file_path, "r", encoding="utf-8") as f:
                after_content = f.readlines()

            # Generate diff in HTML format with highlighting
            diff_html = difflib.HtmlDiff().make_table(before_content, after_content, "Before", "After", context=True)

            # Show diff in the text box
            self.diff_view.insert(tk.END, diff_html)
        except Exception as e:
            self.diff_view.insert(tk.END, f"Error generating diff:\n{e}")

    def commit_and_open(self):
        commit_message = self.commit_entry.get().strip()
        if not commit_message:
            commit_message = "Auto-commit"

        try:
            self.repo.git.add(all=True)  # Stage all changes
            self.repo.index.commit(commit_message)
            self.root.destroy()  # Close the window
            open_in_bambu_studio(self.new_file_path)
        except Exception as e:
            print(f"Git Commit Failed:\n{e}")

    def auto_commit_and_open(self):
        """Auto-commit with actual file name and open file if no changes."""
        commit_message = f"Adding file {self.file_name}"

        try:
            self.repo.git.add(all=True)  # Stage all changes
            self.repo.index.commit(commit_message)
            print(f"Auto-committed: {commit_message}")
        except Exception as e:
            print(f"Git Auto-Commit Failed:\n{e}")

        self.root.destroy()  # Close the window
        open_in_bambu_studio(self.new_file_path)

def copy_file_with_timestamp(src_file, dest_dir):
    """Copy STL file to destination with a timestamp."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(src_file)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_{timestamp}{ext}"
    dest_path = os.path.join(dest_dir, new_filename)

    shutil.copy2(src_file, dest_path)
    return dest_path

def initialize_git_repo(repo_path):
    """Initialize a Git repository if needed."""
    if not os.path.exists(os.path.join(repo_path, ".git")):
        repo = git.Repo.init(repo_path)
        repo.index.commit("Initial commit")
        return repo
    else:
        return git.Repo(repo_path)

def open_in_bambu_studio(file_path):
    """Open the file in Bambu Studio."""
    try:
        subprocess.run(["open", "-a", "/Applications/BambuStudio.app", file_path], check=True)
    except Exception as e:
        print(f"Error opening Bambu Studio:\n{e}")

def get_user_selection():
    """If no command-line args, show file/folder selection dialogs."""
    root = tk.Tk()
    root.withdraw()  # Hide root window

    # Ask for STL file
    stl_file = filedialog.askopenfilename(
        title="Select STL File",
        filetypes=[("STL Files", "*.stl")]
    )
    if not stl_file:
        print("No file selected. Exiting...")
        sys.exit(1)

    # Ask for working directory
    working_dir = filedialog.askdirectory(title="Select Working Directory")
    if not working_dir:
        print("No working directory selected. Exiting...")
        sys.exit(1)

    return stl_file, working_dir

def main():
    if len(sys.argv) < 3:
        print("No command-line arguments detected. Launching file selection dialogs...")
        stl_file, working_dir = get_user_selection()
    else:
        stl_file = sys.argv[1]
        working_dir = sys.argv[2]

    new_file_path = copy_file_with_timestamp(stl_file, working_dir)
    repo = initialize_git_repo(working_dir)

    # Launch Debug Window for Commit
    root = tk.Tk()
    DebugWindow(root, working_dir, new_file_path, repo)
    root.mainloop()

if __name__ == "__main__":
    main()
