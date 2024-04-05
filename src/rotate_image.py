import numpy as np


def rotate_image_fast(img, phi):
    """
    Алгоритм вращения изображения. \n
    https://www.mathworks.com/help/visionhdl/ug/small-angle-rotation-ext-mem.html
    :param img: 2d numpy массив изображения;
    :param phi: Угол поворота (в радианах).
    :return: 2d numpy массив повернутого изображения.
    """
    (height, width) = np.shape(img)

    rotated_image = np.zeros_like(img)
    y_0, x_0 = height / 2, width / 2

    cos_phi, sin_phi = np.cos(phi), np.sin(phi)

    int_x = np.linspace(0, width, width, endpoint=False, dtype=int)
    int_y = np.linspace(0, height, height, endpoint=False, dtype=int)

    mesh_x, mesh_y = np.meshgrid(int_x, int_y)

    float_x = x_0 + cos_phi * (mesh_x - x_0) - sin_phi * (mesh_y - y_0)
    float_y = y_0 + sin_phi * (mesh_x - x_0) + cos_phi * (mesh_y - y_0)

    float_x = np.where((float_x >= 0) & (float_x < width), float_x, 0)
    float_y = np.where((float_y >= 0) & (float_y < height), float_y, 0)

    floor_x = float_x.astype(int)
    floor_y = float_y.astype(int)

    delta_x = float_x - floor_x
    delta_y = float_y - floor_y

    floor_y_1 = np.where((floor_y + 1 < height), floor_y + 1, floor_y)
    floor_x_1 = np.where((floor_x + 1 < width), floor_x + 1, floor_x)

    I1 = img[floor_y, floor_x]
    I2 = img[floor_y_1, floor_x]
    I3 = img[floor_y, floor_x_1]
    I4 = img[floor_y_1, floor_x_1]

    rotated_image = I1 * (1 - delta_x) * (1 - delta_y) + I2 * (1 - delta_x) * delta_y + I3 * delta_x * (
                1 - delta_y) + I4 * delta_x * delta_y

    return rotated_image
