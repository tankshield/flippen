# flippen

**flippen** is a powerful Blender addon for automatically fixing face normals on architectural and general 3D models. It provides a suite of advanced, hybrid, and user-guided methods to make normals consistent, flip only wrongly oriented faces, and handle even the most stubborn or complex geometry.

---

## Features

### 🟢 Smart Normal Correction
- **Flip:** Flips only faces that are wrongly oriented, using a neighbor-consistency check.
- **Persistent Flip:** Runs the neighbor-based method multiple times to catch stubborn or chain-reaction cases.
- **Exterior Heuristic Flip:** Uses ray casting to orient boundary faces based on exposure to empty space, robust for both exteriors and interior rooms.
- **Flood Flip:** Flood-fills from a point outside the mesh, propagating correct orientation to all connected faces.
- **Hybrid Flip:** Combines Persistent Flip with Blender's "Recalculate Outside" for maximum coverage.
- **AO Flip:** Uses ambient occlusion analysis to flip faces that are likely inward-facing based on occlusion.
- **Manual Align:** (Optional) Lets the user select a "correct" face and propagates orientation to all connected faces.

### 🟢 Batch Processing
- The main Flip operator supports batch processing of all selected mesh objects.

### 🟢 User-Friendly Sidebar UI
- All tools are available in the 3D View > Sidebar > **flippen** tab.
- No popups or dialogs—set your options and run with a single click.

### 🟢 Automatic Mode Handling
- Operators automatically switch to Edit Mode if needed.

### 🟢 User Guidance
- Clear instructions and tooltips are provided in the sidebar for each method.

### 🟢 Bug Reporting
- Direct link to the [GitHub repository](https://github.com/tankshield/flippen) for feedback and bug reports in the Addon Preferences.

---

## Installation

1. **Download** the `flippen_02.py` file from this repository.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the `flippen_02.py` file.
4. Enable the addon by checking the box next to "flippen."
5. The tools will appear in the **flippen** tab in the 3D View Sidebar (press `N` to open the sidebar if it's not visible).

---

## Usage

### 1. **Select Your Mesh Object(s)**
- In Object Mode, select the mesh object(s) you want to fix.

### 2. **Open the Sidebar**
- Press `N` in the 3D Viewport to open the sidebar.
- Go to the **flippen** tab.

### 3. **Choose Your Method**
- **Mode Dropdown:** Choose the main operation mode for the Flip button:
  - **Flip Normals:** Neighbor-consistency check.
  - **Make Normals Consistent:** Blender's "Recalculate Outside."
  - **Make Normals Consistent next Flip Normals:** Recalculate then flip all.
- **Max Passes:** Set the number of passes for Persistent Flip and Hybrid Flip.

### 4. **Run the Tools**
- **Flip:** Runs the selected mode from the dropdown.
- **Persistent Flip:** Runs the neighbor-based method multiple times.
- **Hybrid Flip:** Runs Persistent Flip, then Recalculate Outside.
- **AO Flip:** Flips faces with low ambient occlusion (likely inward).
- **Exterior Heuristic Flip:** Uses ray casting to orient boundary faces based on exposure to empty space.
- **Flood Flip:** Flood-fills from outside the mesh to propagate correct orientation.
- **Manual Align:** (Optional) In Edit Mode, select a face you know is correct, then click "Run Manual Align" to propagate orientation.

### 5. **Tips**
- For best results, enable Blender's **Face Orientation** overlay to visually inspect normal directions (blue = outward, red = inward).
- Try different methods in sequence for complex or imported models.
- Use "Flood Flip" or "Exterior Heuristic Flip" for architectural exteriors and rooms.
- Use "Manual Align" for ultimate control in tricky cases.

---

## Example Workflow

1. Select your mesh object.
2. Open the **flippen** tab in the sidebar.
3. Try **Flip** or **Persistent Flip** first.
4. If some faces are still wrong, try **Hybrid Flip**, **Exterior Heuristic Flip**, or **Flood Flip**.
5. For the last few stubborn faces, use **Manual Align**.

---

## Advanced Methods Explained

- **Neighbor Consistency Check:** Flips faces whose normals disagree with the majority of their neighbors.
- **Persistent Flip:** Repeats the neighbor check multiple times to catch chain-reaction errors.
- **Exterior Heuristic Flip:** Uses ray casting to determine if a face is exposed to empty space (exterior) or is interior (e.g., inside a room), and orients accordingly.
- **Flood Flip:** Starts from a point outside the mesh and propagates correct orientation to all connected faces.
- **Hybrid Flip:** Combines Persistent Flip with Blender's "Recalculate Outside" for maximum coverage.
- **AO Flip:** Uses ambient occlusion (ray occlusion) to flip faces that are likely inward-facing.
- **Manual Align:** Lets the user select a "correct" face and propagates orientation to all connected faces.

---

## Bug Reports & Feedback

Please report issues or suggest improvements at [https://github.com/tankshield/flippen](https://github.com/tankshield/flippen).

---

## Credits & About

- Original author: **Alexey Khlystov**
- Fork and major enhancements: **tankshield**
- **Development note:**  
  This addon was forked and edited completely in [Cursor](https://www.cursor.so/) by a person with no prior knowledge of any coding!  
  All improvements and new features were made possible thanks to AI-assisted development.

---

## License

This addon is licensed under the **GNU General Public License v2 or later (GPL-2.0-or-later)**.  
See the LICENSE file for details. 
