#!/usr/bin/env python

import logging

from .flatdict import FlatterDict
import numpy as np
import pandas as pd
import rosbag
from rospy_message_converter.message_converter import convert_ros_message_to_dictionary
from scipy.interpolate import interp1d
# from sensor_msgs.msg import Image, CompressedImage
# from sensor_msgs.msg import CameraInfo
# from cv_bridge import CvBridge, CvBridgeError
import cv2
import os


class RosbagPandaException(Exception):
    pass


def topics_from_keys(keys):
    """
    Extracts the desired topics from specified keys
    :param Keys: List of desired keys
    :return: List of topics
    """
    topics = set()
    for key in keys:
        if not key.startswith("/"):
            key = "/" + key
        chunks = key.split("/")
        for i in range(2, len(chunks)):
            topics.add("/".join(chunks[0:i]))
    return list(topics)


def bag_to_dataframe(bag_name, include=None, exclude=None, output=None):
    """
    Read in a rosbag file and create a pandas data frame that
    is indexed by the time the message was recorded in the bag.

    :param bag_name: String name for the bag file
    :param include: None, or List of Topics to include in the dataframe
    :param exclude: None, or List of Topics to exclude in the dataframe (only applies if include is None)

    :return: a pandas dataframe object
    """
    logging.debug("Reading bag file %s", bag_name)

    bag = rosbag.Bag(bag_name)
    type_topic_info = bag.get_type_and_topic_info()
    topics = type_topic_info.topics.keys()

    image_folder = 'images'
    output_images = os.path.join(output, image_folder)

    try:
        os.makedirs(output_images)
        print("Directory '%s' created" % output_images)
    except FileExistsError as e:
        print("Directory '%s' already exists" % output_images)

    # get list of topics to parse
    logging.debug("Bag topics: %s", topics)

    if not topics:
        raise RosbagPandaException("No topics in bag")

    topics = _get_filtered_topics(topics, include, exclude)
    logging.debug("Filtered bag topics: %s", topics)

    if not topics:
        raise RosbagPandaException("No topics in bag after filtering")

    img_idx = {}
    for topic in topics:
        if "image" in topic:
            image_folder = os.path.join(output_images, topic.split('/')[1])
            if topic not in img_idx:
                img_idx[topic] = {'folder': image_folder, 'counter': 0}
            try:
                os.makedirs(image_folder)
                print("Directory '%s' created" % image_folder)
            except FileExistsError as e:
                print("Directory '%s' already exists" % image_folder)

    data_dict = {}
    for idx, (topic, msg, t) in enumerate(bag.read_messages(topics=topics)):
        flattened_dict = _get_flattened_dictionary_from_ros_msg(msg)
        timestamp = float(str(flattened_dict['header/stamp/secs']) + '.' + str(flattened_dict['header/stamp/nsecs']))

        for key, item in flattened_dict.items():
            if ('header' in key) or ('camera_info' in topic) or ('format' in key):
                continue
            elif 'image' in topic:
                np_arr = np.fromstring(msg.data, np.uint8)
                # image_np = cv2.imdecode(np_arr, cv2.CV_LOAD_IMAGE_COLOR)
                image_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # OpenCV >= 3.0:
                image_path = img_idx[topic]['folder'] + '/' + str(img_idx[topic]['counter']) + '.jpg'
                cv2.imwrite(image_path, image_np)
                img_idx[topic]['counter'] += 1
                # cv2.imshow('cv_img', image_np)
                # cv2.waitKey(0)
                item = image_path.split('images')[1]

            data_key = topic + "/" + key
            if data_key not in data_dict:
                data_dict[data_key] = {'ts': [],
                                       'data': []}

            data_dict[data_key]['ts'].append(timestamp)
            data_dict[data_key]['data'].append(item)

    df = {'timestamp': data_dict['/zed2/zed_node/left/image_rect_color/compressed/data']['ts'],
          'zed2': data_dict['/zed2/zed_node/left/image_rect_color/compressed/data']['data']}
    
    for k, v in data_dict.items():
        if 'zed2' in k:
            continue
        if 'eye' in k:
            indices = [i for i in range(len(data_dict[k]['data']))]
            interpolation_function = interp1d(data_dict[k]['ts'],
                                              indices,
                                              bounds_error=False,
                                              fill_value='extrapolate',
                                              kind='next')
        else:
            interpolation_function = interp1d(data_dict[k]['ts'],
                                              data_dict[k]['data'],
                                              bounds_error=False,
                                              fill_value='extrapolate',
                                              kind='linear')
        if 'eye' in k:
            indices = interpolation_function(data_dict['/zed2/zed_node/left/image_rect_color/compressed/data']['ts'])
            df[k] = [data_dict[k]['data'][int(i)] for i in indices]
        else:
            df[k] = interpolation_function(data_dict['/zed2/zed_node/left/image_rect_color/compressed/data']['ts'])

    bag.close()

    # now we have read all of the messages its time to assemble the dataframe
    df_out = pd.DataFrame(data=df)
    df_out = df_out.sort_values(by=['timestamp'])
    df_out = df_out.reset_index(drop=True)
    df_out.to_csv(output + '/data.csv')


def _get_flattened_dictionary_from_ros_msg(msg):
    """
    Return a flattened python dict from a ROS message
    :param msg: ROS msg instance
    :return: Flattened dict
    """
    return FlatterDict(convert_ros_message_to_dictionary(msg), delimiter="/")


def _get_filtered_topics(topics, include, exclude):
    """
    Filter the topics.
    :param topics: Topics to filter
    :param include: Topics to include if != None
    :param exclude: Topics to exclude if != and include == None
    :return: filtered topics
    """
    logging.debug("Filtering topics (include=%s, exclude=%s) ...", include, exclude)
    return [t for t in include if t in topics] if include is not None else \
        [t for t in topics if t not in exclude] if exclude is not None else topics
