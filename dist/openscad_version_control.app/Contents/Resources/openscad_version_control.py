import sys
import os
import shutil
import time
import subprocess
import git
import tkinter as tk
from tkinter import filedialog, scrolledtext
import difflib

class DebugWindow:
    def __init__(self, root, working_dir, repo):
        self.root = root
        self.root.title("STL Version Control - Debug Window")
        # Get the screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Set window size to match screen dimensions (slightly smaller to avoid overlapping taskbar/dock)
        window_width = screen_width - 20
        window_height = screen_height - 60  # Reduced slightly to account for taskbar/menu bars
        self.root.geometry(f"{window_width}x{window_height}+0+0")

        self.working_dir = working_dir
        self.repo = repo

        self.create_diff_view()

        # Commit Message Entry
        tk.Label(root, text="Commit Message:").pack()
        self.commit_entry = tk.Entry(root, width=50)
        self.commit_entry.pack(pady=5)
        self.root.after(100, self.commit_entry.focus)

        # Commit Button
        self.commit_button = tk.Button(root, text="Commit & Open in Bambu Studio", command=self.commit_and_open)
        self.root.bind('<Enter>', lambda event: self.commit_and_open())
        self.commit_button.pack(pady=10)

        # Auto-commit if no changes
        if not self.has_changes():
            self.auto_commit_and_open()

    def has_changes(self):
        """Check if there are any changes to commit."""
        return bool(self.repo.git.diff())

    def create_diff_view(self):
        """Display before and after file changes side by side with highlighting."""
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        self.diff_text = tk.Text(frame, wrap="none", height=20, width=100)
        self.diff_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, command=self.diff_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.diff_text.config(yscrollcommand=scrollbar.set)

        self.display_side_by_side_diff()

    def commit_and_open(self):
        commit_message = self.commit_entry.get().strip()
        if not commit_message:
            commit_message = "Auto-commit"
        try:
            # Write commit message to macOS Comments file
            new_file_path = copy_file_with_timestamp(stl_file, working_dir)
            file_path = new_file_path
            try:
                set_comment(file_path, commit_message)
                print(f"Added comment to file: {commit_message}")
            except Exception as e:
                print(f"Failed to add macOS comment: {e}")
                
            self.repo.git.add(all=True)  # Stage all changes
            self.repo.index.commit(commit_message)
            self.root.destroy()  # Close the window
            open_in_bambu_studio(new_file_path)
        except Exception as e:
            print(f"Git Commit Failed:\n{e}")

    def auto_commit_and_open(self):
        """Auto-commit with actual file name and open file if no changes."""
        new_file_path = copy_file_with_timestamp(stl_file, working_dir)
        commit_message = f"Adding file {os.path.basename(new_file_path)}"
        try:
            # Write commit message to macOS Comments file
            
            file_path = new_file_path
            try:
                set_comment(file_path, commit_message)
                print(f"Added comment to file: {commit_message}")
            except Exception as e:
                print(f"Failed to add macOS comment: {e}")
                
            self.repo.git.add(all=True)  # Stage all changes
            self.repo.index.commit(commit_message)
            print(f"Auto-committed: {commit_message}")
        except Exception as e:
            print(f"Git Auto-Commit Failed:\n{e}")
        self.root.destroy()  # Close the window
        open_in_bambu_studio(new_file_path)

    def display_side_by_side_diff(self):
        """Main function to display side-by-side diff of .scad files with highlighted changes."""
        try:
            # Find .scad files
            scad_files = self._find_scad_files()
            if not scad_files:
                self.diff_text.insert(tk.END, "No .scad files found in working directory.")
                return
            
            # Setup UI components
            self._setup_diff_ui()
            
            # Process each file
            for scad_file in scad_files:
                self._process_scad_file(scad_file)
            
            # Make text widgets read-only
            self.left_text.config(state=tk.DISABLED)
            self.right_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.handle_general_error(e)

    def _find_scad_files(self):
        """Find all .scad files in the working directory."""
        scad_files = []
        for root, dirs, files in os.walk(self.working_dir):
            for file in files:
                if file.endswith('.scad'):
                    scad_files.append(os.path.join(root, file))
        return scad_files

    def _setup_diff_ui(self):
        """Set up the UI components for the side-by-side diff view."""
        # Remove any existing text widgets
        for widget in self.diff_text.master.winfo_children():
            widget.destroy()
        
        # Create main frame
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left pane
        self._setup_left_pane(frame)
        
        # Create right pane
        self._setup_right_pane(frame)
        
        # Configure text tags
        self._configure_text_tags()
        
        # Synchronize scrolling
        self._setup_scroll_sync()

    def _setup_left_pane(self, parent_frame):
        """Set up the left pane for the previous version."""
        left_frame = tk.Frame(parent_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(left_frame, text="Previous Version", font=("Helvetica", 10, "bold")).pack()
        
        self.left_text = tk.Text(left_frame, wrap=tk.NONE, width=50, height=20)
        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.left_scroll = tk.Scrollbar(left_frame, command=self.left_text.yview)
        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.left_text.config(yscrollcommand=self.left_scroll.set)

    def _setup_right_pane(self, parent_frame):
        """Set up the right pane for the current version."""
        right_frame = tk.Frame(parent_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="Current Version", font=("Helvetica", 10, "bold")).pack()
        
        self.right_text = tk.Text(right_frame, wrap=tk.NONE, width=50, height=20)
        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_scroll = tk.Scrollbar(right_frame, command=self.right_text.yview)
        self.right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.right_text.config(yscrollcommand=self.right_scroll.set)

    def _configure_text_tags(self):
        """Configure highlighting tags for both text widgets."""
        for text_widget in [self.left_text, self.right_text]:
            # Darker/more saturated background colors for better contrast
            text_widget.tag_config("removed", background="#ffb3b3", foreground="black")  # Stronger red
            text_widget.tag_config("added", background="#b3ffb3", foreground="black")    # Stronger green
            text_widget.tag_config("changed", background="#ffe066", foreground="black")  # Stronger yellow
            text_widget.tag_config("placeholder", background="#f0f0f0")  # Light gray background
            
            # Improved contrast for headers
            text_widget.tag_config("header", foreground="#0000cc", font=("Helvetica", 10, "bold"))
            text_widget.tag_config("file_header", foreground="white", background="#304b68", font=("Helvetica", 12, "bold"))

    def _setup_scroll_sync(self):
        """Set up synchronization between the two scrollbars."""
        # Define sync functions
        def sync_scroll_left(*args):
            self.right_text.yview_moveto(self.left_text.yview()[0])
        
        def sync_scroll_right(*args):
            self.left_text.yview_moveto(self.right_text.yview()[0])
        
        # Bind mouse wheel events
        self.left_text.bind("<MouseWheel>", lambda e: [self.left_text.yview_scroll(-1*(e.delta//120), "units"), sync_scroll_left()])
        self.right_text.bind("<MouseWheel>", lambda e: [self.right_text.yview_scroll(-1*(e.delta//120), "units"), sync_scroll_right()])
        
        # Linux mouse wheel bindings
        self.left_text.bind("<Button-4>", lambda e: [self.left_text.yview_scroll(-1, "units"), sync_scroll_left()])
        self.left_text.bind("<Button-5>", lambda e: [self.left_text.yview_scroll(1, "units"), sync_scroll_left()])
        self.right_text.bind("<Button-4>", lambda e: [self.right_text.yview_scroll(-1, "units"), sync_scroll_right()])
        self.right_text.bind("<Button-5>", lambda e: [self.right_text.yview_scroll(1, "units"), sync_scroll_right()])
        
        # Override scrollbar commands
        self.left_scroll.config(command=lambda *args: [self.left_text.yview(*args), sync_scroll_left()])
        self.right_scroll.config(command=lambda *args: [self.right_text.yview(*args), sync_scroll_right()])

    def _process_scad_file(self, scad_file):
        """Process a single .scad file and display its diff."""
        try:
            repo_path = self.repo.working_dir
            rel_path = os.path.relpath(scad_file, repo_path)
            
            # Insert file header
            file_header = f"\n{os.path.basename(scad_file)}\n"
            self.left_text.insert(tk.END, file_header, "file_header")
            self.right_text.insert(tk.END, file_header, "file_header")
            
            # Get file versions
            previous_lines = self.get_previous_version(scad_file, rel_path)
            current_lines = self.get_current_version(scad_file)
            
            # Generate and display diff
            self.display_file_diff(previous_lines, current_lines)
            
        except Exception as e:
            for text_widget in [self.left_text, self.right_text]:
                text_widget.insert(tk.END, f"Error processing {os.path.basename(scad_file)}: {str(e)}\n", "header")

    def get_previous_version(self, scad_file, rel_path):
        """Get the previous version of a file from git."""
        try:
            previous_content = self.repo.git.show(f"HEAD:{rel_path}")
            return previous_content.splitlines()
        except git.exc.GitCommandError:
            self.left_text.insert(tk.END, "(No previous version in git history)\n", "header")
            return []

    def get_current_version(self, scad_file):
        """Get the current version of a file."""
        with open(scad_file, "r", encoding="utf-8") as f:
            return f.read().splitlines()

    def display_file_diff(self, previous_lines, current_lines):
        """Display the diff between two versions of a file."""
        # Use difflib to compute the differences
        matcher = difflib.SequenceMatcher(None, previous_lines, current_lines)
        
        left_line = 0
        right_line = 0
        
        # Process each diff operation
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                left_line = self.add_equal_lines(previous_lines, i1, i2, left_line)
                right_line = self.add_equal_lines(current_lines, j1, j2, right_line, is_right=True)
                
            elif op == 'replace':
                left_line = self.add_changed_lines(previous_lines, i1, i2, left_line)
                right_line = self.add_changed_lines(current_lines, j1, j2, right_line, is_right=True)
                
            elif op == 'delete':
                left_line = self.add_removed_lines(previous_lines, i1, i2, left_line)
                right_line = self.add_placeholder_lines(i2 - i1, right_line, is_right=True)
                
            elif op == 'insert':
                left_line = self.add_placeholder_lines(j2 - j1, left_line)
                right_line = self.add_added_lines(current_lines, j1, j2, right_line)
        
        # Ensure alignment
        self.ensure_equal_lines(left_line, right_line)

    def add_equal_lines(self, lines, start, end, line_count, is_right=False):
        """Add equal (unchanged) lines to the appropriate text widget."""
        text_widget = self.right_text if is_right else self.left_text
        for line in lines[start:end]:
            text_widget.insert(tk.END, line + "\n")
            line_count += 1
        return line_count

    def add_changed_lines(self, lines, start, end, line_count, is_right=False):
        """Add changed lines with highlighting to the appropriate text widget."""
        text_widget = self.right_text if is_right else self.left_text
        for line in lines[start:end]:
            text_widget.insert(tk.END, line + "\n", "changed")
            line_count += 1
        return line_count

    def add_removed_lines(self, lines, start, end, line_count):
        """Add removed lines with highlighting to the left text widget."""
        for line in lines[start:end]:
            self.left_text.insert(tk.END, line + "\n", "removed")
            line_count += 1
        return line_count

    def add_added_lines(self, lines, start, end, line_count):
        """Add added lines with highlighting to the right text widget."""
        for line in lines[start:end]:
            self.right_text.insert(tk.END, line + "\n", "added")
            line_count += 1
        return line_count

    def add_placeholder_lines(self, count, line_count, is_right=False):
        """Add empty placeholder lines to maintain alignment."""
        text_widget = self.right_text if is_right else self.left_text
        for _ in range(count):
            text_widget.insert(tk.END, "\n", "placeholder")
            line_count += 1
        return line_count

    def ensure_equal_lines(self, left_line, right_line):
        """Ensure both text widgets have the same number of lines."""
        if left_line < right_line:
            for _ in range(right_line - left_line):
                self.left_text.insert(tk.END, "\n")
        elif right_line < left_line:
            for _ in range(left_line - right_line):
                self.right_text.insert(tk.END, "\n")

    def handle_general_error(self, error):
        """Handle general errors that occur during diff generation."""
        error_text = tk.Text(self.root)
        error_text.pack(fill=tk.BOTH, expand=True)
        error_text.insert(tk.END, f"Error generating diff:\n{str(error)}\n")
        import traceback
        error_text.insert(tk.END, traceback.format_exc())

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

def set_comment(file_path, comment_text):
    import applescript
    applescript.tell.app("Finder", f'set comment of (POSIX file "{file_path}" as alias) to "{comment_text}" as Unicode text')

def main():
    if len(sys.argv) < 3:
        print("No command-line arguments detected. Launching file selection dialogs...")
        stl_file, working_dir = get_user_selection()
    else:
        stl_file = sys.argv[1]
        working_dir = sys.argv[2]

    repo = initialize_git_repo(working_dir)

    # Launch Debug Window for Commit
    root = tk.Tk()
    DebugWindow(root, working_dir, repo)
    root.mainloop()

if __name__ == "__main__":
    main()
