# SONAR-AI Training Dataset Directory

Follow this standard structure for preparing real Side Scan Sonar (SSS) datasets:

```
dataset/
├── data.yaml
├── images/
│   ├── train/     # 70% of sonar waterfall strips / crops
│   ├── val/       # 20% validation split
│   └── test/      # 10% benchmark split
└── labels/
    ├── train/     # YOLO format .txt annotations (class x_center y_center width height)
    ├── val/
    └── test/
```

### Label Annotation Format
Each row in `.txt` file contains:
`<class_index> <x_center> <y_center> <box_width> <box_height>` (normalized 0.0 - 1.0)

Example:
```
0 0.452 0.312 0.120 0.095
```
(Class 0 = Ghost Net)
