import cv2
import asyncio
import numpy as np
from typing import Optional
from aiortc import VideoStreamTrack
from av import VideoFrame

class CameraVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id: int = 0):
        super().__init__()
        self.camera = cv2.VideoCapture(camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.camera.set(cv2.CAP_PROP_FPS, 30)

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()

        # Read frame from camera
        ret, frame = self.camera.read()
        if not ret:
            # If frame reading failed, create a black frame at 1080p resolution
            frame = np.zeros((1080, 1920, 3), np.uint8)

        # Convert from BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame

    def stop(self):
        """Release camera resources"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None

class CameraManager:
    _instance: Optional['CameraManager'] = None
    _camera_track: Optional[CameraVideoStreamTrack] = None

    @classmethod
    def get_instance(cls) -> 'CameraManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_track(self) -> CameraVideoStreamTrack:
        """Get or create camera track"""
        if self._camera_track is None:
            self._camera_track = CameraVideoStreamTrack()
        return self._camera_track

    def stop_camera(self):
        """Stop camera and release resources"""
        if self._camera_track:
            self._camera_track.stop()
            self._camera_track = None 