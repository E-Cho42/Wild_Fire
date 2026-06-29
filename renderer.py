import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeoMipTerrain, DirectionalLight, AmbientLight, WindowProperties
import numpy as np
from PIL import Image
import data_loader

class WildfireRenderer(ShowBase):
    def __init__(self, elevation: np.ndarray, landcover: np.ndarray):
        ShowBase.__init__(self)
        self.elevation = elevation
        self.landcover = landcover
        self._load_terrain(elevation)
        self._setup_camera()
        self._setup_controls()
        self._setup_lighting()
        self._place_trees(elevation, self.landcover)


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
        
        texture_img = self._create_terrain_texture(elevation)
        texture_img.save("terrain_texture.png")
        texture = self.loader.loadTexture("terrain_texture.png")
        self.terrain_node = terrain
        terrain.getRoot().setTexture(texture)
        terrain.getRoot().reparentTo(self.render)
        terrain.getRoot().setSz(100)

    def _create_terrain_texture(self, elevation):
        elev_min = elevation.min()
        elev_max = elevation.max()
        normalized = (elevation - elev_min) / (elev_max - elev_min)
        color = np.zeros((elevation.shape[0], elevation.shape[1], 3), dtype=np.uint8)
        
        low = normalized <= 0.3
        color[low] = [34, 100, 34]
        mid = (normalized > 0.3) & (normalized <= 0.6)
        color[mid] = [101, 67, 33]
        mid_h = (normalized > 0.6) & (normalized <= 0.85)
        color[mid_h] = [120, 110, 100]
        high = normalized > 0.85
        color[high] = [240, 240, 255]
        return Image.fromarray(color)
    
    def _place_trees(self, elevation, landcover):
        # Get the actual vertical scale factor of the terrain
        terrain_z_scale = self.terrain_node.getRoot().getSz()

        for row in range(0, landcover.shape[0], 15):
            for col in range(0, landcover.shape[1], 15):
                if landcover[row, col] == 10:
                    x = col * (257 / landcover.shape[1])
                    y = row * (257 / landcover.shape[0])
                    
                    # Multiply the 0-1 normalized height by the terrain's Z scale
                    z = self.terrain_node.getElevation(x, y) * terrain_z_scale

                    tree = self.loader.loadModel("models/misc/sphere")
                    tree.setScale(1.5, 1.5, 4)
                    tree.setColor(0.05, 0.4, 0.05, 1)
                    
                    # Now z matches the actual physical surface of the terrain
                    tree.setPos(x, y, z) 
                    tree.setBillboardAxis()
                    tree.reparentTo(self.render)
                    
    def _setup_camera(self):
        self.disableMouse()
        self.camera.setPos(128, 50, 180)
        self.camera.setHpr(0, -20, 0)
        
        # In Panda3D: Heading (Yaw) revolves around Z. Pitch revolves around X.
        self.cam_yaw = 0
        self.cam_pitch = -20
        self.mouse_captured = False

    def _setup_controls(self):
        self.keys = {}
        for key in ["w", "a", "s", "d", "r", "f"]:
            self.keys[key] = False
            self.accept(key,       self._set_key, [key, True])
            self.accept(key+"-up", self._set_key, [key, False])

        # State toggle events
        self.accept("escape", self._release_mouse)
        self.accept("mouse1", self._capture_mouse) # Left click re-enables FPS mode

        # Start with camera captured
        self._capture_mouse()

        self.taskMgr.add(self.update_camera, "update_camera")

    def _capture_mouse(self):
        """Hides mouse and locks it into the center for FPS look."""
        if not self.mouse_captured:
            props = WindowProperties()
            props.setCursorHidden(True)
            # Confine mouse to window if supported by OS
            props.setMouseMode(WindowProperties.M_confined) 
            self.win.requestProperties(props)
            
            # Reset window center to prevent instant camera snaps on click
            self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
            self.mouse_captured = True

    def _release_mouse(self):
        """Unhides mouse and gives control back to desktop."""
        if self.mouse_captured:
            props = WindowProperties()
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            self.win.requestProperties(props)
            self.mouse_captured = False

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

    def update_camera(self, task):
        from panda3d.core import Vec3  # Import Vec3 locally if not imported at top

        # 1. --- MOUSE LOOK (FPS STYLE) ---
        if self.mouse_captured and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            x = md.getX()
            y = md.getY()
            
            cx = self.win.getXSize() // 2
            cy = self.win.getYSize() // 2
            
            dx = x - cx
            dy = y - cy
            
            sensitivity = 0.15
            if dx != 0 or dy != 0:
                self.cam_yaw -= dx * sensitivity
                self.cam_pitch -= dy * sensitivity
                self.cam_pitch = max(-89, min(89, self.cam_pitch))
                
                self.camera.setHpr(self.cam_yaw, self.cam_pitch, 0)
                self.win.movePointer(0, cx, cy)

        # 2. --- KEYBOARD MOVEMENT (FPS STYLE) ---
        if self.mouse_captured:
            speed = 2.5
            
            # Use Panda3D's native vector system
            dir_forward = self.render.getRelativeVector(self.camera, Vec3(0, 1, 0))
            dir_right = self.render.getRelativeVector(self.camera, Vec3(1, 0, 0))
            
            # Flatten to prevent flying or sinking while moving forward
            dir_forward.setZ(0)
            dir_right.setZ(0)
            dir_forward.normalize()
            dir_right.normalize()

            # Initialize a native Panda3D Vec3 instead of a numpy array
            move_vec = Vec3(0, 0, 0)
            if self.keys["w"]: move_vec += dir_forward
            if self.keys["s"]: move_vec -= dir_forward
            if self.keys["a"]: move_vec -= dir_right
            if self.keys["d"]: move_vec += dir_right
            
            # Explicit vertical climbing
            if self.keys["r"]: move_vec.setZ(move_vec.getZ() + 1)
            if self.keys["f"]: move_vec.setZ(move_vec.getZ() - 1)

            # Apply movement to current position using Panda3D addition
            cur_pos = self.camera.getPos()
            self.camera.setPos(cur_pos + (move_vec * speed))

        return task.cont

if __name__ == "__main__":
    lat = -43.5231
    long = 172.5794
    elevation = data_loader.download_elevation(lat, long)
    landcover = data_loader.download_landcover(lat, long)
    landcover = data_loader.align_landcover(landcover, elevation)
    app = WildfireRenderer(elevation, landcover)
    app.run()