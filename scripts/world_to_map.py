#!/usr/bin/env python3

import argparse
import math
import os
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw


def parse_pose(element):
    """
    读取 SDF 的 <pose>：
    x y z roll pitch yaw
    """
    pose_element = element.find("pose")

    if pose_element is None or not pose_element.text:
        return 0.0, 0.0, 0.0, 0.0

    values = [float(v) for v in pose_element.text.split()]

    while len(values) < 6:
        values.append(0.0)

    x, y, z, _, _, yaw = values[:6]
    return x, y, z, yaw


def compose_pose(parent_pose, child_pose):
    """
    将子坐标系位姿转换到父坐标系。
    这里只处理导航地图需要的 x、y、z、yaw。
    """
    px, py, pz, pyaw = parent_pose
    cx, cy, cz, cyaw = child_pose

    cos_yaw = math.cos(pyaw)
    sin_yaw = math.sin(pyaw)

    world_x = px + cos_yaw * cx - sin_yaw * cy
    world_y = py + sin_yaw * cx + cos_yaw * cy
    world_z = pz + cz
    world_yaw = pyaw + cyaw

    return world_x, world_y, world_z, world_yaw


class WorldToMap:
    def __init__(
        self,
        xmin,
        xmax,
        ymin,
        ymax,
        resolution,
        min_obstacle_z,
        max_obstacle_z,
    ):
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.resolution = resolution

        self.min_obstacle_z = min_obstacle_z
        self.max_obstacle_z = max_obstacle_z

        self.width = math.ceil((xmax - xmin) / resolution)
        self.height = math.ceil((ymax - ymin) / resolution)

        # 254 表示自由空间，0 表示障碍物
        self.image = Image.new("L", (self.width, self.height), 254)
        self.draw = ImageDraw.Draw(self.image)

        self.box_count = 0
        self.cylinder_count = 0
        self.mesh_count = 0

    def world_to_pixel(self, x, y):
        column = int(round((x - self.xmin) / self.resolution))

        # PGM 图像从上向下，而 ROS 地图 y 轴从下向上
        row = self.height - 1 - int(
            round((y - self.ymin) / self.resolution)
        )

        return column, row

    def height_intersects(self, center_z, size_z):
        bottom_z = center_z - size_z / 2.0
        top_z = center_z + size_z / 2.0

        return (
            top_z >= self.min_obstacle_z
            and bottom_z <= self.max_obstacle_z
        )

    def draw_box(self, pose, size):
        x, y, z, yaw = pose
        size_x, size_y, size_z = size

        if not self.height_intersects(z, size_z):
            return

        half_x = size_x / 2.0
        half_y = size_y / 2.0

        local_corners = [
            (-half_x, -half_y),
            (half_x, -half_y),
            (half_x, half_y),
            (-half_x, half_y),
        ]

        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)

        pixels = []

        for local_x, local_y in local_corners:
            world_x = x + cos_yaw * local_x - sin_yaw * local_y
            world_y = y + sin_yaw * local_x + cos_yaw * local_y

            pixels.append(self.world_to_pixel(world_x, world_y))

        self.draw.polygon(pixels, fill=0)
        self.box_count += 1

    def draw_cylinder(self, pose, radius, length):
        x, y, z, _ = pose

        if not self.height_intersects(z, length):
            return

        pixels = []

        point_count = 48

        for index in range(point_count):
            angle = 2.0 * math.pi * index / point_count

            world_x = x + radius * math.cos(angle)
            world_y = y + radius * math.sin(angle)

            pixels.append(self.world_to_pixel(world_x, world_y))

        self.draw.polygon(pixels, fill=0)
        self.cylinder_count += 1

    def process_collision(self, collision, parent_pose):
        collision_pose = compose_pose(
            parent_pose,
            parse_pose(collision),
        )

        geometry = collision.find("geometry")

        if geometry is None:
            return

        box = geometry.find("box")

        if box is not None:
            size_text = box.findtext("size")

            if size_text:
                size = [float(value) for value in size_text.split()]

                if len(size) == 3:
                    self.draw_box(collision_pose, size)

            return

        cylinder = geometry.find("cylinder")

        if cylinder is not None:
            radius_text = cylinder.findtext("radius")
            length_text = cylinder.findtext("length")

            if radius_text and length_text:
                self.draw_cylinder(
                    collision_pose,
                    float(radius_text),
                    float(length_text),
                )

            return

        mesh = geometry.find("mesh")

        if mesh is not None:
            self.mesh_count += 1

    def process_link(self, link, model_pose):
        link_pose = compose_pose(
            model_pose,
            parse_pose(link),
        )

        for collision in link.findall("collision"):
            self.process_collision(collision, link_pose)

    def process_model(self, model, parent_pose=(0.0, 0.0, 0.0, 0.0)):
        model_pose = compose_pose(
            parent_pose,
            parse_pose(model),
        )

        for link in model.findall("link"):
            self.process_link(link, model_pose)

        # 支持嵌套 model
        for nested_model in model.findall("model"):
            self.process_model(nested_model, model_pose)

    def process_world_file(self, world_file):
        tree = ET.parse(world_file)
        root = tree.getroot()

        world = root.find("world")

        if world is None and root.tag == "world":
            world = root

        if world is None:
            raise RuntimeError("文件中没有找到 <world> 节点")

        for model in world.findall("model"):
            self.process_model(model)

    def save(self, output_prefix):
        output_directory = os.path.dirname(output_prefix)

        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

        pgm_path = output_prefix + ".pgm"
        yaml_path = output_prefix + ".yaml"

        self.image.save(pgm_path)

        image_filename = os.path.basename(pgm_path)

        yaml_content = f"""image: {image_filename}
resolution: {self.resolution}
origin: [{self.xmin}, {self.ymin}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""

        with open(yaml_path, "w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml_content)

        print("地图生成完成")
        print(f"PGM:  {pgm_path}")
        print(f"YAML: {yaml_path}")
        print(f"图片尺寸: {self.width} × {self.height}")
        print(f"Box 数量: {self.box_count}")
        print(f"Cylinder 数量: {self.cylinder_count}")

        if self.mesh_count:
            print(
                f"警告：发现 {self.mesh_count} 个 mesh，"
                "该脚本暂未解析 mesh 几何。"
            )


def main():
    parser = argparse.ArgumentParser(
        description="将 Gazebo world/sdf 静态碰撞体转换为 ROS PGM 地图"
    )

    parser.add_argument("world_file")
    parser.add_argument("output_prefix")

    parser.add_argument("--xmin", type=float, required=True)
    parser.add_argument("--xmax", type=float, required=True)
    parser.add_argument("--ymin", type=float, required=True)
    parser.add_argument("--ymax", type=float, required=True)

    parser.add_argument(
        "--resolution",
        type=float,
        default=0.05,
    )

    parser.add_argument(
        "--min-obstacle-z",
        type=float,
        default=0.05,
        help="低于该高度的物体不作为障碍物",
    )

    parser.add_argument(
        "--max-obstacle-z",
        type=float,
        default=1.5,
        help="高于该范围且不与机器人高度相交的物体不作为障碍物",
    )

    args = parser.parse_args()

    converter = WorldToMap(
        xmin=args.xmin,
        xmax=args.xmax,
        ymin=args.ymin,
        ymax=args.ymax,
        resolution=args.resolution,
        min_obstacle_z=args.min_obstacle_z,
        max_obstacle_z=args.max_obstacle_z,
    )

    converter.process_world_file(args.world_file)
    converter.save(args.output_prefix)


if __name__ == "__main__":
    main()
