import os
import sys
import json
import datetime
import rasterio
from rasterio.windows import Window
from shapely.geometry import box
from shapely.validation import make_valid
import geopandas as gpd
import cv2
from tqdm import tqdm


def geotiff_to_coco_tiles(
    geotiff_path,
    geojson_path,
    class_field,
    output_dir="output_coco",
    tile_size=1000,
 #   class_field="tipocase",
    overlap=200,
    output_format="jpg"
):
    os.makedirs(output_dir, exist_ok=True)
    img_out_dir = os.path.join(output_dir, "images")
    os.makedirs(img_out_dir, exist_ok=True)

    ann_out_path = os.path.join(output_dir, "annotations_coco.json")

    # Load  geotiff image
    dataset = rasterio.open(geotiff_path)
    width, height = dataset.width, dataset.height
    transform = dataset.transform

    # Load  polygons
    gdf = gpd.read_file(geojson_path)
    gdf = gdf.to_crs(dataset.crs)  # check same  CRS

    # Map  "class_field" categories from  GeoJSON file
    categories = []
    category_map = {}
    if class_field not in gdf:
      print("ERROR - we cannot find your attribute in GeoJson.Did you insert the correct attribute?")
      sys.exit()
    for i, cls in enumerate(sorted(gdf[class_field].unique())):
        categories.append({"id": i, "name": cls, "supercategory": "objects"})
        category_map[cls] = i

    # COCO structure
    coco_output = {
        "info": {
            "year": str(datetime.datetime.now().year),
            "version": "1.0",
            "description": "Dataset COCO generated from GeoTIFF and GeoJSON",
            "contributor": "Lindo Nepi",
            "url": "",
            "date_created": datetime.datetime.now().isoformat()
        },
        "licenses": [
            {
                "id": 1,
                "url": "https://creativecommons.org/licenses/by/4.0/",
                "name": "CC BY 4.0"
            }
        ],
        "images": [],
        "annotations": [],
        "categories": categories
    }

    ann_id = 1
    img_id = 1

    # Scan  tile
    step = tile_size - overlap
    for y in tqdm(range(0, height, step)):
        for x in range(0, width, step):
            if x + tile_size > width or y + tile_size > height:
                continue  # drop incomplete  tiles

            window = Window(x, y, tile_size, tile_size)
            tile = dataset.read(window=window)
            tile = tile.transpose((1, 2, 0))  # CHW -> HWC

            out_img_name = f"tile_{img_id}.{output_format}"
            out_img_path = os.path.join(img_out_dir, out_img_name)
            cv2.imwrite(out_img_path, cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))

            # Info  COCO image
            coco_output["images"].append({
                "id": img_id,
                "license": 1,
                "file_name": out_img_name,
                "height": tile_size,
                "width": tile_size,
                "date_captured": datetime.datetime.now().isoformat()
            })

            # Bounding box tile with  Geo coordinates 
            tile_bounds = rasterio.windows.bounds(window, transform)
            tile_geom = box(*tile_bounds)

            # Intersections  polygons - tiles 
            for _, row in gdf.iterrows():
                poly = row.geometry
                if not poly.is_valid:
                    poly = make_valid(poly)
                if poly.is_empty:
                    continue

                if poly.intersects(tile_geom):
                    inter = poly.intersection(tile_geom)
                    if inter.is_empty:
                        continue

                    # Coordinate pixel relative alla tile
                    coords = []
                    try:
                        exterior = inter.exterior.coords
                    except AttributeError:
                        continue  # geometria non poligonale
                    for xg, yg in exterior:
                        px, py = ~dataset.transform * (xg, yg)  # world -> pixel
                        px -= x
                        py -= y
                        coords.extend([px, py])

                    if len(coords) < 6:
                        continue  # check if polygon has at leat  3 points

                    x_coords = coords[0::2]
                    y_coords = coords[1::2]
                    x_min, y_min = min(x_coords), min(y_coords)
                    x_max, y_max = max(x_coords), max(y_coords)
                    w = x_max - x_min
                    h = y_max - y_min

                    coco_output["annotations"].append({
                        "id": ann_id,
                        "image_id": img_id,
                        "category_id": category_map[row[class_field]],
                        "bbox": [float(x_min), float(y_min), float(w), float(h)],
                        "area": float(w * h),
                        "segmentation": [coords],  # nested LIST
                        "iscrowd": 0
                    })
                    ann_id += 1

            img_id += 1

    # Save COCO JSON
    with open(ann_out_path, "w", encoding="utf-8") as f:
        json.dump(coco_output, f, indent=2)

    print(f"✅ Tiles saved in {img_out_dir}")
    print(f"✅ COCO JSON saved in {ann_out_path}")


# === SET PARAMETERS HERE ===

class_field_input=input("Which QGIS attribute do you want to use to identify COCO labels?")


geotiff_to_coco_tiles(
 # your geoTiff image path and filename 
    geotiff_path="test-monticellitif2.tif",
 # your geoJson file path and filename 
    geojson_path="geojson-test-monticelli.geojson",
# attribute name in QGIS used to create COCO labels 
#    class_field="tipocase",
    class_field=class_field_input,
# set output data 
    output_dir="dataset_coco180925",
# pixel size for tiles
    tile_size=1000,
# number of pixels for overlap 
    overlap=200,
    output_format="jpg"
)
