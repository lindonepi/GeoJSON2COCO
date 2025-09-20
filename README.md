# GeoJSON2COCO
Convert your  GIS geojson files  into COCO annotations useful for training an automatic segmentation model 

If you use GIS systems, you can use the shapefiles (in geojson format) you obtain to create useful annotations for training a computer vision model to recognise and segment objects. 

This script allows you to do this. Simply enter  the parameters in the script with the names of the Geotiff image files you want to analyse and your shapefile in geojson format.
You can also set the tile size (the initial file is cropped into many tiles of the same size to improve training) and the pixel overlap value between tiles (typically a value of 20% or 30% of the tile size is used).
Also indicate the folder that will contain the COCO annotations and images.

You must also enter the name of the field (attribute) that you used in your GIS system to indicate the labels of each object in the GeoJSON file. This value will be used to create the labels linked to the annotations.  

After running the script, you will find the file with the COCO annotations and the tile images   in the specified output folder. (file format = JPG)

If you want to use your COCO annotation file with software such as YOLO, you must first use a COCO2YOLO-Seg  ( https://github.com/z00bean/coco2yolo-seg/blob/main/COCO2YOLO-seg.py) script to generate annotations in YOLO format. You can use other scripts to convert COCO to other formats such as VOC.

If, on the other hand, you want to convert YOLOv11 segmentation output (predictions) to GeoJSON format, you can use my script YOLOv11Seg2GeoJSON ( link 
https://github.com/lindonepi/Yolov11Seg2GeoJSON )

