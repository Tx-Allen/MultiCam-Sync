# MultiCam Sync / 多机位同步

MultiCam Sync is a Python-based application designed to load, synchronize, and control multiple video streams simultaneously. The tool provides both local and global controls for playback, navigation, screenshot capture, and time-based jump features. Screenshots are automatically organized into folders based on each video’s filename.

MultiCam Sync 是一个基于 Python 的应用程序，旨在同时加载、同步和控制多个视频流。该工具提供了本地和全局控制，可用于播放、导航、截图和基于时间跳转的功能。截图会自动按视频文件名归档保存。

---

## Features / 功能

- **Multi-Video Support / 多视频支持**  
  Load multiple videos, which are displayed in a two‑column grid layout.  
  支持加载多个视频，以两列网格布局显示。

- **Time Synchronization / 时间同步**  
  - **OCR Detection:** Automatically perform OCR on the first frame of each video. If successful, the video's start time is set to the OCR result and the end time is set to start time + 5 minutes.  
    **OCR检测：**自动对每个视频的第一帧进行OCR检测；若成功，则将视频的起始时间设为OCR结果，结束时间设为起始时间加5分钟。  
  - **Manual Input:** Manually set start and end times if OCR fails.  
    **手动输入：**如果OCR失败，可手动设置起始和结束时间。

- **Playback and Navigation / 播放与导航**  
  - **Local Controls:** Each video item has its own play, pause, screenshot, and navigation controls. Navigation includes a shared spinbox for both rewind and fast‑forward using two buttons ("Rewind" and "Fast Forward").  
    **本地控制：**每个视频项都有独立的播放、暂停、截图和导航控制。导航控制包括一个共享的偏移量输入框，用于回退和快进（通过“Rewind”和“Fast Forward”按钮实现）。  
  - **Global Controls:** The main window provides global operations including play all, pause all, global rewind and fast‑forward (using a single global offset spinbox), global jump-to-time, and multi‑screenshot with interval.  
    **全局控制：**主窗口提供全局操作，如同时播放、同时暂停、全局回退和快进（共用一个全局偏移量输入框）、全局跳转时间以及带间隔的多次截图。

- **Screenshot Organization / 截图管理**  
  - **Screenshots are saved under the folder structure:**
    **screenshots/ <video_filename_without_extension>/ <remark><frame>.png (if a remark is provided) or screenshot<frame>.png (if no remark is provided)**
  - **截图将保存在以下文件夹结构中：**
    **screenshots/ <视频文件名（无扩展名）>/ <备注><帧数>.png （如果有备注） 或 screenshot<帧数>.png （如果未设置备注）**


- **Additional Features / 其他功能**  
  - **Hide/Show Info:** Toggle button to hide or display video-related information.  
    **隐藏/显示信息：** 切换按钮用于隐藏或显示视频信息。  
  - **Copy Path:** Copy the video file path to the clipboard.  
    **复制路径：** 将视频文件路径复制到剪贴板。  
  - **Delete Video:** Remove a video item from the grid; the grid layout refreshes automatically.  
    **删除视频：** 从网格中删除视频项，网格会自动刷新以填补空位。  
  - **Global Jump-to-Time:** Enter a time to jump all videos to the corresponding frame.  
    **全局跳转时间：** 输入时间后，所有视频将跳转到对应帧。

- **Logging / 日志记录**  
All notifications are output to a log panel using colored text:  
  - **Red:** for errors.  
    **红色**：表示错误。  
  - **Dark Green:** for success messages.  
    **深绿色**：表示成功信息。  
  - **Black:** for general information.  
    **黑色**：表示普通信息。

---

## Installation / 安装

### Prerequisites / 先决条件
- **Python 3.8**  
- **PyQt5**  
- **OpenCV**  
- **pytesseract**


### Usage / 使用说明
Clone or Download the Project
Clone the repository from GitHub or download the source code.
从 GitHub 克隆仓库或下载源代码。

Run the Application
In the project root directory, run:
在项目根目录下运行：
python main.py

Application Overview / 应用概述

Adding Videos:
Click the "Add Video" button to select one or more video files. They will appear in a 2‑column grid layout.
**添加视频：**点击“Add Video”按钮选择一个或多个视频文件，视频会以两列网格显示。

Automatic OCR:
Each video automatically performs OCR on its first frame. If successful, the video's start time is set to the OCR result and the end time is set to start + 5 minutes.
**自动OCR：**每个视频自动对第一帧进行OCR检测；若成功，则起始时间设置为OCR结果，结束时间为起始时间加5分钟。

Local Controls:
Each video item has its own controls for play, pause, screenshot, and navigation. Navigation uses a single spinbox for both Rewind and Fast Forward.
**本地控制：**每个视频项都有独立的播放、暂停、截图和导航控制。导航使用同一个输入框进行回退和快进操作。

Global Controls:
The main window provides global operations including play all, pause all, global rewind and fast-forward (using a shared spinbox), global jump-to-time, and multi‑screenshot with interval.
**全局控制：**主窗口提供全局操作，如同时播放、同时暂停、全局回退和快进（共用一个输入框）、全局跳转时间以及带间隔的多次截图。

Logging:
All operations and notifications are logged in the output panel using colored text (red for errors, dark green for successes, black for general info).
**日志记录：**所有操作和通知都通过彩色文本记录在日志面板中（红色表示错误，深绿色表示成功，黑色表示普通信息）。

Screenshot Storage:
Screenshots are saved under the folder screenshots/ in a subfolder named after the video file (without extension).
**截图存储：**截图保存在 screenshots/ 文件夹下的以视频文件名（无扩展名）命名的子文件夹中，文件名格式为 <remark>_<frame>.png 或 screenshot_<frame>.png。

Hide/Show Info and Deletion:
Each video item has a toggle button to hide or show video-related information and a delete button to remove the video from the grid.
**隐藏/显示信息及删除：**每个视频项都有一个切换按钮用于隐藏或显示视频信息，并有删除按钮以从网格中移除视频。

Global Jump-to-Time:
Enter a time in the global jump-to-time field and click the "Jump All to Time" button to make all videos jump to the corresponding frame.
**全局跳转时间：**在全局跳转时间输入框中输入时间，然后点击“Jump All to Time”按钮，所有视频将跳转到对应帧。

Project Structure / 项目结构

MultiCam-Sync/
├── main.py              # Application entry point
├── player/
│   ├── __init__.py      # (Empty)
│   ├── multi_video_player.py  # Main window and global controls
│   └── video_item.py    # VideoItem class with local controls
└── README.md            # This file
main.py: Entry point of the application.
**main.py：**应用程序入口。

player/multi_video_player.py: Contains the main window class and global controls.
**player/multi_video_player.py：**包含主窗口类和全局控制。

player/video_item.py: Contains the VideoItem class that manages individual videos and local controls.
**player/video_item.py：**包含管理各视频项及其本地控制的 VideoItem 类。

