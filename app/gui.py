import json
import sqlite3
import threading
import tkinter as tk
from tkinter import messagebox, ttk
# Import backend crawler engine and storage helper functions
from element_crawler import ElementCrawler, export_to_csv, export_to_sqlite


class CrawlerGUI:
    """
    Main Application Window Class.
    Handles user inputs, triggers non-blocking background web crawling,
    and updates the interactive results table dynamically.
    """

    def __init__(self, root):
        # Attach and configure main application window
        self.root = root
        self.root.title("Web Crawler")
        self.root.geometry("900x650")  # Set default window dimensions (width x height)

        # 1.Top container for input fields and buttons
        control_frame = ttk.LabelFrame(
            root, text="Crawler Controls", padding=10
        )
        # Pack stretches panel horizontally across top of window
        control_frame.pack(fill="x", padx=10, pady=5)

        # Seed URLs Input Row
        ttk.Label(control_frame, text="Seed URLs (comma-separated):").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.url_entry = ttk.Entry(control_frame, width=60)
        self.url_entry.pack_forget()  # Safeguard against accidental packing before grid layout
        self.url_entry.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.url_entry.insert(0, "")  # Initialize empty input box for custom entry

        # Crawl Depth Input Row
        ttk.Label(control_frame, text="Max Depth:").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.depth_entry = ttk.Entry(control_frame, width=10)
        self.depth_entry.insert(0, "1")  # Default to 1-level deep traversal
        self.depth_entry.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        # Keyword Matching Input Row
        ttk.Label(
            control_frame, text="Target Keywords (comma-separated):"
        ).grid(row=2, column=0, sticky="w", pady=4)
        self.keywords_entry = ttk.Entry(control_frame, width=60)
        self.keywords_entry.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        # Script Footprint Input Row
        ttk.Label(
            control_frame, text="Target Scripts (comma-separated):"
        ).grid(row=3, column=0, sticky="w", pady=4)
        self.scripts_entry = ttk.Entry(control_frame, width=60)
        self.scripts_entry.grid(row=3, column=1, sticky="w", padx=5, pady=4)

        # Action Trigger Button
        self.run_btn = ttk.Button(
            control_frame, text="Start Crawl", command=self.start_crawl_thread
        )
        self.run_btn.grid(row=4, column=1, sticky="e", pady=10)

        # Real-Time Status Bar
        self.status_label = ttk.Label(
            root, text="Status: Ready", font=("Arial", 10, "italic")
        )
        self.status_label.pack(anchor="w", padx=15, pady=2)

        # 2. Bottom container for data display
        table_frame = ttk.LabelFrame(
            root, text="Discovered Match Results", padding=10
        )
        # Stretches table container to fill remaining window space
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Configure tabular column structure using Treeview
        columns = ("url", "depth", "matched_features")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Define column header labels
        self.tree.heading("url", text="Target URL")
        self.tree.heading("depth", text="Depth")
        self.tree.heading("matched_features", text="Matched Signatures")

        # Set column widths and alignment
        self.tree.column("url", width=320)
        self.tree.column("depth", width=60, anchor="center")
        self.tree.column("matched_features", width=480)

        # Add vertical scrollbar for large output datasets
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscroll=scrollbar.set)

        # Position elements inside table container
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def start_crawl_thread(self):
        """
        Input Validation & Thread Dispatcher:
        Fired when 'Start Crawl' is clicked. Validates user input, disables 
        the action button to prevent duplicate runs, clears existing GUI table data, 
        and offloads network execution to a daemon background thread.
        """
        raw_urls = self.url_entry.get().strip()
        if not raw_urls:
            messagebox.showwarning(
                "Input Missing", "Please enter at least one Seed URL to crawl."
            )
            return

        # Disable button & update UI indicator so user knows background work started
        self.run_btn.config(state="disabled")
        self.status_label.config(text="Status: Crawling in progress...")

        # Clear prior scan results from table UI
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Spawn non blocking background thread for heavy crawling operations
        thread = threading.Thread(target=self.run_crawler, daemon=True)
        thread.start()

    def run_crawler(self):
        """
        Background Crawler Execution Pipeline:
        Runs outside main UI thread. Extracts input field text, structures target payload, 
        invokes crawler engine, triggers CSV/SQLite exports, and safely passes findings back to UI thread.
        """
        try:
            # Parse comma separated seed URLs into clean list
            raw_urls = self.url_entry.get().strip()
            seed_urls = [
                u.strip() for u in raw_urls.split(",") if u.strip()
            ]

            # Validate depth input; fallback to depth 1 if non numeric string given
            try:
                max_depth = int(self.depth_entry.get().strip())
            except ValueError:
                max_depth = 1

            # Parse target keywords into list
            raw_keywords = self.keywords_entry.get().strip()
            keywords = [
                k.strip() for k in raw_keywords.split(",") if k.strip()
            ]

            # Parse target JS script footprints into list
            raw_scripts = self.scripts_entry.get().strip()
            scripts = [s.strip() for s in raw_scripts.split(",") if s.strip()]

            # Build inspection rules configuration dictionary dynamically
            targets = {}
            if keywords:
                targets["keywords"] = keywords
            if scripts:
                targets["scripts"] = scripts

            # Fallback DOM structural element selectors
            targets["selectors"] = [
                "form[action*='subscribe']",
                "input[type='email']",
            ]

            # Initialize backend crawler engine & execute network crawl
            crawler = ElementCrawler(
                target_elements=targets, max_depth=max_depth
            )
            results = crawler.crawl(seed_urls)

            # Persist findings to disk (CSV & SQLite storage pipelines)
            export_to_csv(results, filename="crawl_results.csv")
            export_to_sqlite(results, db_name="crawl_results.db")

            # Safely schedule display refresh on main thread via root.after()
            self.root.after(0, self.display_results, results)

        except Exception as e:
            # Trap runtime exceptions, alert user, and re enable action button
            self.root.after(
                0, lambda: messagebox.showerror("Error", f"Execution error: {e}")
            )
            self.root.after(
                0,
                lambda: self.status_label.config(
                    text="Status: Error during crawl."
                ),
            )
            self.root.after(0, lambda: self.run_btn.config(state="normal"))

    def display_results(self, results):
        """
        Main Thread UI Updater:
        Receives crawled datasets and populates rows into the Tkinter Treeview table widget.
        """
        for item in results:
            self.tree.insert(
                "",
                "end",
                values=(item["url"], item["depth"], item["matched_features"]),
            )

        # Update status bar with match count & re enable Start button for next run
        self.status_label.config(
            text=f"Status: Finished. Discovered {len(results)} match(es)."
        )
        self.run_btn.config(state="normal")


# Application Entry Point
if __name__ == "__main__":
    root = tk.Tk()
    app = CrawlerGUI(root)
    root.mainloop()  # Launches Tkinter event loop