from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeoMipTerrain, DirectionalLight, AmbientLight
import numpy as np
from PIL import Image
import math

class WildfireRenderer(ShowBase):
    def __init__(self, elevation: np.ndarray):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.53, 0.70, 0.85, 1)
        self._load_terrain(elevation)
        self._setup_camera()
        self._setup_controls()
        self._setup_lighting()

    def _load_terrain(self, elevation):
        elev_min = elevation.min()
        elev_max = elevation.max()
        normalized = (elevation - elev_min) / (elev_max - elev_min) * 255
        img = Image.fromarray(normalized.astype(np.uint8))
        img = img.resize((257, 257))
        img.save("heightmap.png")
        terrain = GeoMipTerrain("terrain")
        terrain.setHeightfield("heightmap.png")
        terrain.setBlockSize(64)
        terrain.generate()
        terrain.getRoot().reparentTo(self.render)
        terrain.getRoot().setSz(100)

    def _setup_camera(self):
        self.disableMouse()
        self.camera.setPos(128, -200, 150)
        self.camera.lookAt(128, 128, 0)
        self.cam_yaw    = 0
        self.cam_pitch  = -30
        self.cam_dist   = 300
        self.cam_target = (128, 128, 0)

    def _setup_controls(self):
        self.keys = {}
        for key in ["w", "a", "s", "d", "q", "e", "r", "f"]:
            self.keys[key] = False
            self.accept(key,       self._set_key, [key, True])
            self.accept(key+"-up", self._set_key, [key, False])

        self.accept("mouse1",    self._start_drag)
        self.accept("mouse1-up", self._stop_drag)
        self.dragging   = False
        self.last_mouse = None
        self.taskMgr.add(self._update_camera, "update_camera")

    def _setup_lighting(self):
        sun = DirectionalLight("sun")
        sun.setColor((1, 0.9, 0.7, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(45, -45, 0)
        self.render.setLight(sun_np)

        ambient = AmbientLight("ambient")
        ambient.setColor((0.3, 0.3, 0.4, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

    def _set_key(self, key, val):
        self.keys[key] = val

    def _start_drag(self):
        self.dragging = True
        self.last_mouse = None

    def _stop_drag(self):
        self.dragging = False

    def _update_camera(self, task):
        speed = 2.0
        if self.keys["w"]: self.cam_target = (self.cam_target[0], self.cam_target[1] - speed, self.cam_target[2])
        if self.keys["s"]: self.cam_target = (self.cam_target[0], self.cam_target[1] + speed, self.cam_target[2])
        if self.keys["a"]: self.cam_target = (self.cam_target[0] + speed, self.cam_target[1], self.cam_target[2])
        if self.keys["d"]: self.cam_target = (self.cam_target[0] - speed, self.cam_target[1], self.cam_target[2])
        if self.keys["q"]: self.cam_dist = max(50,  self.cam_dist - 3)
        if self.keys["e"]: self.cam_dist = min(600, self.cam_dist + 3)
        if self.keys["r"]: self.cam_target = (self.cam_target[0], self.cam_target[1], self.cam_target[2] + speed)
        if self.keys["f"]: self.cam_target = (self.cam_target[0], self.cam_target[1], self.cam_target[2] - speed)

        if self.dragging and self.mouseWatcherNode.hasMouse():
            mx = self.mouseWatcherNode.getMouseX()
            my = self.mouseWatcherNode.getMouseY()
            if self.last_mouse:
                dx = mx - self.last_mouse[0]
                dy = my - self.last_mouse[1]
                self.cam_yaw   -= dx * 80
                self.cam_pitch += dy * 40
                self.cam_pitch  = max(-80, min(-5, self.cam_pitch))
            self.last_mouse = (mx, my)

        yaw_r   = math.radians(self.cam_yaw)
        pitch_r = math.radians(self.cam_pitch)
        cx = self.cam_target[0] + self.cam_dist * math.cos(pitch_r) * math.sin(yaw_r)
        cy = self.cam_target[1] + self.cam_dist * math.cos(pitch_r) * math.cos(yaw_r)
        cz = self.cam_target[2] + self.cam_dist * math.sin(-pitch_r)
        self.camera.setPos(cx, cy, cz)
        self.camera.lookAt(*self.cam_target)
        return task.cont


from data_loader import download_elevation

elevation = download_elevation(39.7555, -105.2211)
app = WildfireRenderer(elevation)
app.run()