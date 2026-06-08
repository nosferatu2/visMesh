import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit)
from PyQt5.QtCore import Qt

class MeshTweakGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenFOAM Bounding Box & STL Real-Time Aligner")
        self.setGeometry(100, 100, 1200, 900)
        
        # Default Domain
        self.xmin, self.xmax = -2.0, 3.0
        self.ymin, self.ymax = -1.25, 1.25
        self.zmin, self.zmax = -0.8, 0.5
        
        # Default STL Position Offset
        self.obj_x, self.obj_y, self.obj_z = 0.0, 0.0, 0.0
        
        self.stl_path = "constant/triSurface/lenz.stl"
        
        self.init_ui()
        self.load_base_stl()
        self.update_visualization()

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # ----------------------------------------------------
        # LEFT SIDE: Status, 3D Canvas, and Object Shifts
        # ----------------------------------------------------
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        
        self.lbl_status = QLabel("Status: OK")
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: green; padding: 4px;")
        left_layout.addWidget(self.lbl_status)
        
        self.plotter = QtInteractor(self)
        left_layout.addWidget(self.plotter.interactor)
        
        obj_group = QGroupBox("Object Position Offset (X, Y, Z)")
        obj_layout = QHBoxLayout(obj_group)
        
        self.txt_obj_x = QLineEdit(str(self.obj_x))
        self.txt_obj_y = QLineEdit(str(self.obj_y))
        self.txt_obj_z = QLineEdit(str(self.obj_z))
        
        obj_layout.addWidget(QLabel("X Shift:"))
        obj_layout.addWidget(self.txt_obj_x)
        obj_layout.addWidget(QLabel("Y Shift:"))
        obj_layout.addWidget(self.txt_obj_y)
        obj_layout.addWidget(QLabel("Z Shift:"))
        obj_layout.addWidget(self.txt_obj_z)
        
        left_layout.addWidget(obj_group)
        main_layout.addWidget(left_container, stretch=3)
        
        # ----------------------------------------------------
        # RIGHT SIDE: Input Matrix & Copy-Paste Export Block
        # ----------------------------------------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setFixedWidth(320)
        
        # Bounds Fields Group
        bounds_group = QGroupBox("Bounding Box Bounds")
        bounds_layout = QVBoxLayout(bounds_group)
        
        self.txt_xmin = QLineEdit(str(self.xmin))
        self.txt_xmax = QLineEdit(str(self.xmax))
        self.txt_ymin = QLineEdit(str(self.ymin))
        self.txt_ymax = QLineEdit(str(self.ymax))
        self.txt_zmin = QLineEdit(str(self.zmin))
        self.txt_zmax = QLineEdit(str(self.zmax))
        
        bounds_layout.addWidget(QLabel("Min X (Inlet):"))
        bounds_layout.addWidget(self.txt_xmin)
        bounds_layout.addWidget(QLabel("Max X (Outlet):"))
        bounds_layout.addWidget(self.txt_xmax)
        bounds_layout.addSpacing(5)
        
        bounds_layout.addWidget(QLabel("Min Y (Right Wall):"))
        bounds_layout.addWidget(self.txt_ymin)
        bounds_layout.addWidget(QLabel("Max Y (Left Wall):"))
        bounds_layout.addWidget(self.txt_ymax)
        bounds_layout.addSpacing(5)
        
        bounds_layout.addWidget(QLabel("Min Z (Floor):"))
        bounds_layout.addWidget(self.txt_zmin)
        bounds_layout.addWidget(QLabel("Max Z (Ceiling):"))
        bounds_layout.addWidget(self.txt_zmax)
        
        right_layout.addWidget(bounds_group)
        
        # Clipboard Output Group
        output_group = QGroupBox("blockMeshDict Paste Output")
        output_layout = QVBoxLayout(output_group)
        
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setFontFamily("Courier New")
        self.txt_output.setFontPointSize(9.5)
        self.txt_output.setToolTip("Highlight and copy this exact text for your blockMeshDict file.")
        output_layout.addWidget(self.txt_output)
        
        right_layout.addWidget(output_group)
        
        # Push Button
        btn_update = QPushButton("Update Viewport & Code")
        btn_update.setStyleSheet("background-color: #2b78e4; color: white; font-weight: bold; padding: 8px; font-size: 12px;")
        btn_update.clicked.connect(self.sync_inputs)
        right_layout.addWidget(btn_update)
        
        main_layout.addWidget(right_panel, stretch=1)

    def load_base_stl(self):
        try:
            self.raw_stl_mesh = pv.read(self.stl_path)
        except Exception as e:
            self.raw_stl_mesh = pv.Sphere(radius=0.2)
            print(f"Using fallback sphere geometry. Error: {e}")

    def sync_inputs(self):
        try:
            self.xmin = float(self.txt_xmin.text())
            self.xmax = float(self.txt_xmax.text())
            self.ymin = float(self.txt_ymin.text())
            self.ymax = float(self.txt_ymax.text())
            self.zmin = float(self.txt_zmin.text())
            self.zmax = float(self.txt_zmax.text())
            
            self.obj_x = float(self.txt_obj_x.text())
            self.obj_y = float(self.txt_obj_y.text())
            self.obj_z = float(self.txt_obj_z.text())
            
            self.update_visualization()
        except ValueError:
            self.lbl_status.setText("Status: Error — Invalid non-numeric entry found")
            self.lbl_status.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")

    def update_visualization(self):
        self.plotter.clear()
        self.plotter.add_axes()
        self.plotter.show_grid()
        
        # 1. Translate and Render STL Mesh
        shifted_mesh = self.raw_stl_mesh.copy()
        shifted_mesh.translate([self.obj_x, self.obj_y, self.obj_z], inplace=True)
        self.plotter.add_mesh(shifted_mesh, color="white", smooth_shading=True, name="stl_obj")
        
        # 2. Check Enclosure Boundaries
        stl_bounds = shifted_mesh.bounds
        warnings = []
        if stl_bounds[0] < self.xmin: warnings.append("Front Inlet (Min X)")
        if stl_bounds[1] > self.xmax: warnings.append("Rear Outlet (Max X)")
        if stl_bounds[2] < self.ymin: warnings.append("Right Wall (Min Y)")
        if stl_bounds[3] > self.ymax: warnings.append("Left Wall (Max Y)")
        if stl_bounds[4] < self.zmin: warnings.append("Floor Boundary (Min Z)")
        if stl_bounds[5] > self.zmax: warnings.append("Ceiling Boundary (Max Z)")
        
        if len(warnings) > 0:
            box_color = "red"
            status_text = f"WARNING: STL Out of Bounds! -> Check: {', '.join(warnings)}"
            status_style = "color: red; font-weight: bold; font-size: 13px; background-color: #ffe6e6; padding: 4px;"
        else:
            box_color = "lightgreen"
            status_text = "Status: OK (STL is safely completely enclosed)"
            status_style = "color: green; font-weight: bold; font-size: 13px; background-color: #e6ffe6; padding: 4px;"
            
        self.lbl_status.setText(status_text)
        self.lbl_status.setStyleSheet(status_style)
        
        # 3. Compile the 8 explicit coordinates
        v0 = [self.xmin, self.ymin, self.zmin]
        v1 = [self.xmax, self.ymin, self.zmin]
        v2 = [self.xmax, self.ymax, self.zmin]
        v3 = [self.xmin, self.ymax, self.zmin]
        v4 = [self.xmin, self.ymin, self.zmax]
        v5 = [self.xmax, self.ymin, self.zmax]
        v6 = [self.xmax, self.ymax, self.zmax]
        v7 = [self.xmin, self.ymax, self.zmax]
        
        vertices = np.array([v0, v1, v2, v3, v4, v5, v6, v7])
        faces = np.array([[4,0,1,2,3], [4,4,5,6,7], [4,0,1,5,4], [4,1,2,6,5], [4,2,3,7,6], [4,3,0,4,7]]).flatten()
        tunnel_box = pv.PolyData(vertices, faces)
        
        # 4. Render Background wireframe
        self.plotter.add_mesh(tunnel_box, color=box_color, opacity=0.12, style="surface")
        self.plotter.add_mesh(tunnel_box, color="black", style="wireframe", line_width=2)
        
        # 5. Red Center Sphere (0,0,0)
        self.plotter.add_mesh(pv.Sphere(radius=0.03, center=(0,0,0)), color="red")
        self.plotter.reset_camera()
        
        # 6. Format and Write out the Dictionary Text Segment
        dict_text = (
            "vertices\n"
            "(\n"
            f"    ({v0[0]:.4f} {v0[1]:.4f} {v0[2]:.4f})    // vertex 0\n"
            f"    ({v1[0]:.4f} {v1[1]:.4f} {v1[2]:.4f})    // vertex 1\n"
            f"    ({v2[0]:.4f} {v2[1]:.4f} {v2[2]:.4f})    // vertex 2\n"
            f"    ({v3[0]:.4f} {v3[1]:.4f} {v3[2]:.4f})    // vertex 3\n"
            f"    ({v4[0]:.4f} {v4[1]:.4f} {v4[2]:.4f})    // vertex 4\n"
            f"    ({v5[0]:.4f} {v5[1]:.4f} {v5[2]:.4f})    // vertex 5\n"
            f"    ({v6[0]:.4f} {v6[1]:.4f} {v6[2]:.4f})    // vertex 6\n"
            f"    ({v7[0]:.4f} {v7[1]:.4f} {v7[2]:.4f})    // vertex 7\n"
            ");"
        )
        self.txt_output.setPlainText(dict_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MeshTweakGUI()
    window.show()
    sys.exit(app.exec_())
