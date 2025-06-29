#!/usr/bin/env python3
"""
YOLO 모델을 사용한 Bird Poop 면적 계산 스크립트
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def calculate_birdpoo_area(model_path, image_path, confidence=0.5):
    """
    단일 이미지에서 Bird Poop 면적 계산
    """
    model = YOLO(model_path)
    results = model(image_path, conf=confidence)
    
    total_area = 0
    areas = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i, box in enumerate(boxes):
                # 바운딩 박스 좌표
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # 면적 계산 (픽셀 단위)
                area = (x2 - x1) * (y2 - y1)
                areas.append(area)
                total_area += area
                
                print(f"Bird Poop {i+1}: {area:.2f} 픽셀²")
    
    print(f"총 면적: {total_area:.2f} 픽셀²")
    print(f"평균 면적: {np.mean(areas):.2f} 픽셀²")
    
    return areas, total_area

def calculate_area_in_real_units(model_path, image_path, reference_object_size_mm, confidence=0.5):
    """
    실제 단위(mm, cm 등)로 면적 계산
    reference_object_size_mm: 이미지에서 알려진 크기의 참조 객체 크기(mm)
    """
    model = YOLO(model_path)
    results = model(image_path, conf=confidence)
    
    # 이미지 크기
    img = cv2.imread(image_path)
    img_height, img_width = img.shape[:2]
    
    # 픽셀당 실제 크기 계산 (참조 객체 필요)
    # 예: 이미지에서 10cm 크기의 객체가 100픽셀이라면
    # 픽셀당 1mm가 됨
    pixel_to_mm = reference_object_size_mm / 100  # 예시값, 실제로는 참조 객체로 계산
    
    total_area_mm2 = 0
    areas_mm2 = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # 픽셀 면적
                area_pixels = (x2 - x1) * (y2 - y1)
                
                # 실제 면적 (mm²)
                area_mm2 = area_pixels * (pixel_to_mm ** 2)
                areas_mm2.append(area_mm2)
                total_area_mm2 += area_mm2
                
                print(f"Bird Poop {i+1}: {area_mm2:.2f} mm²")
    
    print(f"총 면적: {total_area_mm2:.2f} mm²")
    print(f"평균 면적: {np.mean(areas_mm2):.2f} mm²")
    
    return areas_mm2, total_area_mm2

def calculate_area_by_size_category(model_path, image_path, confidence=0.5):
    """
    크기별로 면적 분류 및 계산
    """
    model = YOLO(model_path)
    results = model(image_path, conf=confidence)
    
    size_categories = {
        'small': {'count': 0, 'total_area': 0, 'areas': []},
        'medium': {'count': 0, 'total_area': 0, 'areas': []},
        'large': {'count': 0, 'total_area': 0, 'areas': []}
    }
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                
                # 크기별 분류
                if area < 1000:
                    size_categories['small']['count'] += 1
                    size_categories['small']['total_area'] += area
                    size_categories['small']['areas'].append(area)
                elif area < 5000:
                    size_categories['medium']['count'] += 1
                    size_categories['medium']['total_area'] += area
                    size_categories['medium']['areas'].append(area)
                else:
                    size_categories['large']['count'] += 1
                    size_categories['large']['total_area'] += area
                    size_categories['large']['areas'].append(area)
    
    print("크기별 면적 분석:")
    for size, data in size_categories.items():
        if data['count'] > 0:
            avg_area = data['total_area'] / data['count']
            print(f"  {size}: {data['count']}개, 총면적 {data['total_area']:.2f}픽셀², 평균면적 {avg_area:.2f}픽셀²")
    
    return size_categories

def calculate_coverage_percentage(model_path, image_path, confidence=0.5):
    """
    이미지에서 Bird Poop이 차지하는 비율 계산
    """
    model = YOLO(model_path)
    results = model(image_path, conf=confidence)
    
    # 이미지 크기
    img = cv2.imread(image_path)
    img_height, img_width = img.shape[:2]
    total_image_area = img_height * img_width
    
    total_birdpoo_area = 0
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                total_birdpoo_area += area
    
    coverage_percentage = (total_birdpoo_area / total_image_area) * 100
    
    print(f"이미지 전체 면적: {total_image_area} 픽셀²")
    print(f"Bird Poop 총 면적: {total_birdpoo_area:.2f} 픽셀²")
    print(f"커버리지 비율: {coverage_percentage:.2f}%")
    
    return coverage_percentage

def visualize_area_analysis(model_path, image_path, confidence=0.5):
    """
    면적 분석 결과를 시각화
    """
    model = YOLO(model_path)
    results = model(image_path, conf=confidence)
    
    # 이미지에 면적 정보 추가
    annotated_image = results[0].plot()
    
    areas = []
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                area = (x2 - x1) * (y2 - y1)
                areas.append(area)
                
                # 바운딩 박스 위에 면적 표시
                cv2.putText(annotated_image, f'{area:.0f}px²', 
                           (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 총 면적 정보 추가
    total_area = sum(areas)
    cv2.putText(annotated_image, f'Total Area: {total_area:.0f}px²', 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return annotated_image

if __name__ == "__main__":
    # 훈련된 모델 경로
    model_path = "redistributed_birdpoo_training/yolo11n_redistributed/weights/best.pt"
    
    print("=== Bird Poop 면적 계산 기능 ===")
    print("1. 기본 면적 계산")
    print("2. 실제 단위 면적 계산")
    print("3. 크기별 면적 분류")
    print("4. 커버리지 비율 계산")
    print("5. 면적 시각화")
    
    # 예시 사용법
    # image_path = "test_image.jpg"
    # areas, total_area = calculate_birdpoo_area(model_path, image_path)
    # coverage = calculate_coverage_percentage(model_path, image_path)
    # annotated_img = visualize_area_analysis(model_path, image_path)
    # cv2.imwrite("area_analysis.jpg", annotated_img)
    
    print("\n스크립트가 준비되었습니다!")
    print("실제 이미지 경로를 지정하여 사용하세요.") 