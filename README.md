# rosbag_pandas
based on [this](https://github.com/eurogroep/rosbag_pandas) repository.

## Scripts

### bag_csv

Convert a ROS bag file to a CSV file and extract the images in image topics in separate folders. The image paths are found in the csv file.
```
usage: bag_csv [-h] [-b BAG] [-i [INCLUDE [INCLUDE ...]]]
               [-e [EXCLUDE [EXCLUDE ...]]] [-o OUTPUT] [-v]

Script to parse bagfile to csv file and extract images to jpeg format.

optional arguments:
  -h, --help            show this help message and exit
  -b BAG, --bag BAG     Bag file to read
  -i [INCLUDE [INCLUDE ...]], --include [INCLUDE [INCLUDE ...]]
                        List for topics to include
  -e [EXCLUDE [EXCLUDE ...]], --exclude [EXCLUDE [EXCLUDE ...]]
                        List for topics to exclude
  -o OUTPUT, --output OUTPUT
                        path of the output folder
  -v, --verbose         Log verbose
```

### bag_plot
not implemented yet

### bag_print
not implemented yet


Python library (and some tools) for converting [ROS bagfiles](http://wiki.ros.org/rosbag) to [Pandas dataframes](https://pandas.pydata.org/).

## Python library

```python
import rosbag_pandas

# Convert a ROSBag to a dataframe
df = rosbag_pandas.bag_to_dataframe('data/rosout.bag')
df_exclude = rosbag_pandas.bag_to_dataframe('data/example.bag', exclude=['/scan'])
df_include = rosbag_pandas.bag_to_dataframe('data/rosout.bag', include=['/rosout'])

# Select a dataframe key based on topic and (conform msgevalgen pattern http://docs.ros.org/api/rostopic/html/)
print(df['/rosout/header/stamp/secs'].to_string())

# Obtain possible ROS topics from a selection pattern (conform msgevalgen pattern http://docs.ros.org/api/rostopic/html/)
# This will return the possible topics: /pose, /pose/pose, /pose/pose/position
rosbag_pandas.topics_from_keys(["/pose/pose/position/x"])
```

## Key definition

Key definition conform the msgevalgen pattern http://docs.ros.org/api/rostopic/html/). Example:

```
/pose/pose/position/x
```

This will select the `/pose/position/x` property of topic `/pose` in the message of type http://docs.ros.org/api/geometry_msgs/html/msg/PoseStamped.html.
