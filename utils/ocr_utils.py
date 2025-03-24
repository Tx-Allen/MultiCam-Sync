#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import pytesseract
import re
from datetime import datetime

def extract_time_from_frame(frame, roi=(0,0,250,40)):
    """
    OCR识别 "YYYY-MM-DD HH:MM:SS"
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    x,y,w,h = roi
    roi_frame = gray[y:y+h, x:x+w]

    _, thresh = cv2.threshold(roi_frame, 128,255, cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(thresh)
    # debug
    #print("[DEBUG] OCR raw:", repr(text))

    pattern = r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"
    m = re.search(pattern, text)
    if m:
        try:
            dt= datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
            return dt
        except:
            return None
    return None
