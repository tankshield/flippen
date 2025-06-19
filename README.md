**flippen**

flippen is a Blender addon forked with cursor, for automatically fixing face normals on multiple objects. It provides a streamlined workflow for architectural and general 3D models, making normals consistent and flipping only those that are wrongly oriented.

**Features**

Batch Normal Correction: Fix normals on multiple selected mesh objects at once.

Three Modes of Operation:

Flip Normals: Flips only the faces that are wrongly oriented (inward-facing) based on the majority normal direction.

Make Normals Consistent: Uses Blender’s built-in “Recalculate Outside” to make all normals point outward, matching Blender’s Face Orientation overlay (blue = outside).

Make Normals Consistent then Flip Normals: First makes normals consistent, then flips all normals.

Simple UI: Access the operator from the Object menu in the 3D Viewport.

Supports Blender 4.4 and later.

**Installation**

Download the flippen_01.py file from this repository.

In Blender, go to Edit > Preferences > Add-ons.

Click Install... and select the flippen_01.py file.

Enable the addon by checking the box next to “flippen.”

The operator will be available in the Object menu in the 3D Viewport.

**Usage**

Select one or more mesh objects in Object Mode.

Go to the Object menu in the 3D Viewport.

Choose flippen.

In the operator panel (bottom left of the viewport or F9), select the desired mode:

Flip Normals

Make Normals Consistent

Make Normals Consistent next Flip Normals

The addon will process all selected objects and fix their normals according to your chosen mode.

**Tips**

For best results, enable Blender’s Face Orientation overlay to visually inspect normal directions (blue = outward, red = inward).
The “Make Normals Consistent” mode is equivalent to Blender’s “Recalculate Outside” and is the most robust for closed (manifold) meshes.


This addon is licensed under the GNU General Public License v2 or later (GPL-2.0-or-later).
See the LICENSE file for details.

**Credits**

Original author: Alexey Khlystov

Fork and modifications:tankshield

Based on the flippist_blender addon.

**Contributing**
Pull requests and suggestions are welcome! Please open an issue or submit a PR.
