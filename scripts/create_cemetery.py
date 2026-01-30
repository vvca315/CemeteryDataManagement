from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsPointXY
)
from qgis.PyQt.QtCore import QVariant
import processing

# -----------------------------
# User Parameters
# -----------------------------
cemetery_layer_name = "section"  # Replace with your polygon layer name
dx = 1.2   # horizontal spacing (meters)
dy = 2.5   # vertical spacing (meters)
starting_lot = 463
section_code = "00C"
output_csv = r"E:\\cemetery_graves.csv"  # change path

# -----------------------------
# 1. Get polygon layer
# -----------------------------
cemetery_layers = QgsProject.instance().mapLayersByName(cemetery_layer_name)
if not cemetery_layers:
    raise Exception(f"Layer '{cemetery_layer_name}' not found")
cemetery_layer = cemetery_layers[0]

# -----------------------------
# 2. Create grid points inside polygon
# -----------------------------
grid_result = processing.run("qgis:creategrid", {
    'TYPE': 0,  # Point grid
    'EXTENT': cemetery_layer.extent(),
    'HSPACING': dx,
    'VSPACING': dy,
    'CRS': cemetery_layer.crs(),
    'OUTPUT': 'memory:grid_points'
})

grid_layer = grid_result['OUTPUT']

# -----------------------------
# 3. Clip points to polygon
# -----------------------------
clipped_result = processing.run("qgis:clip", {
    'INPUT': grid_layer,
    'OVERLAY': cemetery_layer,
    'OUTPUT': 'memory:clipped_points'
})

points_layer = clipped_result['OUTPUT']

# -----------------------------
# 4. Add lot, col, and grave_id fields
# -----------------------------
points_layer.dataProvider().addAttributes([
    QgsField("lot", QVariant.Int),
    QgsField("col", QVariant.Int),
    QgsField("grave_id", QVariant.String)
])
points_layer.updateFields()

# Compute extents for indexing
x_min = points_layer.extent().xMinimum()
y_max = points_layer.extent().yMaximum()

# -----------------------------
# 5. Assign lot, col, grave_id
# -----------------------------
points_layer.startEditing()
for f in points_layer.getFeatures():
    x = f.geometry().asPoint().x()
    y = f.geometry().asPoint().y()
    
    col = int((x - x_min) / dx) + 1
    lot = int((y_max - y) / dy) + starting_lot
    grave_id = f"{section_code}{str(lot).zfill(3)}{str(col).zfill(3)}"
    
    f["col"] = col
    f["lot"] = lot
    f["grave_id"] = grave_id
    points_layer.updateFeature(f)

points_layer.commitChanges()

# -----------------------------
# 6. Add the layer to QGIS
# -----------------------------
QgsProject.instance().addMapLayer(points_layer)
print("Grid points layer added to QGIS project.")

# -----------------------------
# 7. Export to CSV
# -----------------------------
error = QgsVectorFileWriter.writeAsVectorFormat(
    points_layer,
    output_csv,
    "UTF-8",
    points_layer.crs(),
    "CSV",
    layerOptions=['GEOMETRY=AS_XY']
)

if error == QgsVectorFileWriter.NoError:
    print(f"CSV exported successfully to: {output_csv}")
else:
    print("Error exporting CSV")
