import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "GPU 없음")

from ultralytics import YOLO

if __name__ == '__main__':
    # Load a model
    model = YOLO("yolo11n.yaml")  # build a new model from YAML
    model = YOLO("yolo11n.pt")  # load a pretrained model (recommended for training)
    model = YOLO("yolo11n.yaml").load("yolo11n.pt")  # build from YAML and transfer weights

    results = model.train(data="my-project/Parrot Puzzle.v2i.yolov11/data.yaml", epochs=100, imgsz=640)