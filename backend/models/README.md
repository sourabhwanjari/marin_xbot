# SONAR-AI Custom Weights Directory

Place your custom-trained YOLO weights in this directory named:
```
sonar_best.pt
```

### Supported Format
- Standard Ultralytics YOLO PyTorch checkpoint (`.pt`).
- Classes expected (5 classes):
  - `0`: `ghost_net`
  - `1`: `shipwreck`
  - `2`: `pipe`
  - `3`: `cylinder`
  - `4`: `debris`

### Behavior
- When `sonar_best.pt` exists, the detector automatically switches to **AI MODEL ACTIVE** mode and executes real inference.
- When `sonar_best.pt` is missing, the detector defaults safely to **DEMO MODE** with labeled deterministic sample detections for testing and presentation purposes.
