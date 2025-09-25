+        TIMEOUTS_DISABLED_PERIODS = [
+            "Game Starts in:",
+            "Half Time",
+            "Overtime Game Break",
+            "Sudden Death Game Break",
+            "Overtime First Half",
+            "Overtime Half Time",
+            "Overtime Second Half",
+            "Sudden Death",
+        ]
+        # Always enable penalties during Referee Time-Out, even if entered from Game Starts in
+        if cur_period['name'] == "Referee Time-Out":
+            self.penalties_button.config(state=tk.NORMAL)
+            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
+            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
+        elif cur_period['name'] in TIMEOUTS_DISABLED_PERIODS:
+            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
+            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
+            if cur_period['name'] in ["Game Starts in:", "Between Game Break", "Half Time", "Overtime Game Break", "Sudden Death Game Break"]:
+                self.penalties_button.config(state=tk.DISABLED)
+            else:
+                self.penalties_button.config(state=tk.NORMAL)
+        elif cur_period['name'] == "Between Game Break":
+            self.white_timeout_button.config(state=tk.NORMAL, bg="white", fg="black")
+            self.black_timeout_button.config(state=tk.NORMAL, bg="black", fg="white")
+            self.penalties_button.config(state=tk.DISABLED)
+        else:
+            self.white_timeout_button.config(state=tk.NORMAL, bg="white", fg="black")
+            self.black_timeout_button.config(state=tk.NORMAL, bg="black", fg="white")
+            self.penalties_button.config(state=tk.NORMAL)
