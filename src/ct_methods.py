import numpy as np
from .rotate_image import rotate_image_fast


def get_projections_fast(img, angle_ticks):
    """
    Функция получения проекций объекта (изображения) под разными
    углами. \n
    :param img: 2d numpy массив изображения;
    :param angle_ticks: число равноотдаленных отсчетов углов проекций;
        Угол проекции меняется от 0 до pi.
    :return: projections, angles - полученные проекции и их соответствующие им углы (в радианах).
    """
    angles = np.linspace(0, np.pi, angle_ticks, endpoint=False)
    img_size = np.shape(img)[0]
    projections = []
    for i in range(angle_ticks):
        if i != 0:
            rotated_img = rotate_image_fast(img, angles[i])
        else:
            rotated_img = img[:, :]
        projection = []
        for y in range(img_size):
            projection.append(np.sum(rotated_img[y]))

        projections.append(projection)

    return projections, angles

def iter_reconstruction_fast(img, projections, angles, iters, interrupt_event, progress):
    """
    Функция итерационного восстановления изображения из проекций.
    :param img: тайл (tile) одной из проекций в projections;
    :param projections: массив проекций изображения;
    :param angles:  углы, которые соответствуют проекциям;
    :param iters:   число итераций.
    :return: 2d numpy массив восстановленного изображения.
    """
    img_size = np.shape(img)[0]
    angle_ticks = np.shape(angles)[0]
    rotated_img = img[:, :]
    for it in range(iters):
        for i in range(angle_ticks):
            if i != 0:
                rotated_img = rotate_image_fast(rotated_img, angles[i] - angles[i - 1])

            for y in range(img_size):
                row_sum = np.sum(rotated_img[y])
                if row_sum == 0 and projections[i][y] == 0:
                    continue
                elif row_sum == 0:
                    rotated_img[y] = np.ones_like(rotated_img[y]) * projections[i][y] / img_size
                elif projections[i][y] == 0:
                    rotated_img[y] = np.zeros_like(rotated_img[y])
                else:
                    scalar = row_sum / projections[i][y]
                    rotated_img[y] = rotated_img[y] / scalar
        
        rotated_img = rotate_image_fast(rotated_img, -angles[angle_ticks - 1])
        if interrupt_event.is_set():
            break
        progress.progress_event.emit(int(100 * it / (iters - 1)))

    return rotated_img

def ct_iter(img, angle_ticks, iters, interrupt_event, progress):
    """
    Итерационное восстановление изображения.
    :param img: 2d numpy массив изображения;
    :param angle_ticks: число равноотдаленных отсчетов углов проекций.
        Угол проекции меняется от 0 до pi;
    :param iters: число итераций.
    :return: 2d numpy массив восстановленного изображения.
    """

    pad_width = (int(np.shape(img)[0] * np.sqrt(2)) - np.shape(img)[0]) // 2
    pad_width = int(1.5 * pad_width)
    padded_image = np.pad(img, pad_width=pad_width)
    padded_image = padded_image.astype(float)

    projs, angles = get_projections_fast(padded_image, angle_ticks)

    padded_img_tile = np.tile(np.array([projs[0]]).transpose(), (1, np.shape(projs)[1]))

    reconstructed_image = iter_reconstruction_fast(padded_img_tile, projs, angles, iters, interrupt_event, progress)
    return reconstructed_image

