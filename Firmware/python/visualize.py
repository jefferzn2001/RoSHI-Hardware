import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from imu_reader import IMUReader
import time

class IMUVisualizer:
    def __init__(self):
        self.imu = IMUReader()
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.setup_plot()
        self.blocks = {}  # Store block objects for each IMU
        self.colors = ['r', 'g', 'b', 'y']  # Colors for different IMUs
        self.last_update = time.time()
        self.update_interval = 0.01  # 100Hz
        
    def setup_plot(self):
        """Setup the 3D plot"""
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_xlim([-2, 2])
        self.ax.set_ylim([-2, 2])
        self.ax.set_zlim([-2, 2])
        self.ax.grid(True)
        plt.title('IMU 3D Orientation')
        
    def create_block_vertices(self):
        """Create vertices for a rectangular block"""
        l, w, h = 0.3, 0.5, 0.1  # length, width, height
        vertices = np.array([
            [-l, -w, -h], [l, -w, -h], [l, w, -h], [-l, w, -h],
            [-l, -w, h], [l, -w, h], [l, w, h], [-l, w, h]
        ])
        return vertices

    def create_block_faces(self, vertices):
        """Create faces for the block"""
        faces = [
            [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
            [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
            [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
            [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
            [vertices[0], vertices[3], vertices[7], vertices[4]],  # left
            [vertices[1], vertices[2], vertices[6], vertices[5]]   # right
        ]
        return faces

    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion to rotation matrix"""
        w, x, y, z = q['w'], q['i'], q['j'], q['k']
        return np.array([
            [1 - 2*y*y - 2*z*z,     2*x*y - 2*z*w,     2*x*z + 2*y*w],
            [    2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z,     2*y*z - 2*x*w],
            [    2*x*z - 2*y*w,     2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
        ])

    def update(self, frame):
        """Update function for animation"""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return self.ax.collections
            
        data = self.imu.read()
        if not data:
            return self.ax.collections
            
        # Remove all existing collections
        for collection in self.ax.collections[:]:
            collection.remove()
        
        for imu_id, imu_data in data.items():
            # Skip entries that don't have quaternion (e.g., button tracker 0)
            if 'quaternion' not in imu_data:
                continue
            color = self.colors[imu_id % len(self.colors)]
            
            # Create or update block
            vertices = self.create_block_vertices()
            rotation_matrix = self.quaternion_to_rotation_matrix(imu_data['quaternion'])
            rotated_vertices = np.dot(vertices, rotation_matrix.T)
            
            # Add offset based on IMU ID to separate blocks
            offset = np.array([0, (imu_id - 1) * 1.0, 0])
            faces = self.create_block_faces(rotated_vertices)
            faces = [f + offset for f in faces]
            
            # Create block
            poly = Poly3DCollection(faces, alpha=0.9)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            self.ax.add_collection3d(poly)
            
            # Add text label
            center = offset + [0, 0, 0.3]
            self.ax.text(center[0], center[1], center[2], 
                        f'IMU #{imu_id}\nBatt: {imu_data["battery"]}%',
                        horizontalalignment='center')
        
        self.last_update = current_time
        return self.ax.collections

    def wait_for_imus(self, timeout=5.0):
        """Wait for IMUs to be detected"""
        print("Waiting for IMUs", end="", flush=True)
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = self.imu.read()
            if data:
                print("\nDetected IMUs:")
                self.imu.list()
                return True
            print(".", end="", flush=True)
            time.sleep(0.1)
        print("\nNo IMUs detected after timeout!")
        return False

    def run(self):
        """Run the visualization"""
        print("Starting 3D visualization...")
        
        # Wait for IMUs to be detected
        if not self.wait_for_imus():
            return
        
        # Create animation at 100Hz
        ani = FuncAnimation(
            self.fig, self.update, interval=10,  # Request frames at 100Hz
            blit=True, cache_frame_data=False
        )
        
        plt.show()

if __name__ == "__main__":
    visualizer = IMUVisualizer()
    visualizer.run() 