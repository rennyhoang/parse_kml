from fastkml import kml
from fastkml import geometry as kml_geometry
from shapely import geometry as shapely_geometry
import pickle
import os.path
import numpy as np
import h5py


def latlon2yx(lon, lat):
    # 33.50 34.4 -118.75 -117.25
    lat0 = 34.4
    lon0 = -118.75
    step = 0.00277778

    y = -int((lat - lat0) / step)
    x = int((lon - lon0) / step)

    return x, y


# load polygon and check if point inside
def in_polygon(coord):
    """ return a bool for whether or not coord in polygon """
    with open('polygon.pickle', 'rb') as handle:
        polygon = pickle.load(handle)
    point = shapely_geometry.Point(coord)
    return polygon.contains(point)


# for saving basins/polygon to file
def save_to_file(file_name, saved_object):
    with open(file_name, 'wb') as handle:
        pickle.dump(saved_object, handle, protocol=-1)


# parse the KML file to get basins
def create_basin_dict(file_name):
    """ return a dictionary mapping names -> polygons """
    basin_dict = {}

    # recursively search through KML for placemarks
    def parse_placemarks(document):
        for feature in document:
            if isinstance(feature, kml.Placemark):
                nonlocal basin_dict
                placemark = feature
                parse_polygon(basin_dict, placemark)
            elif isinstance(feature, kml.Folder) or isinstance(feature, kml.Document):
                parse_placemarks(list(feature.features()))

    with open(file_name, 'r') as file:
        file_content = file.read()

    k = kml.KML()
    k.from_string(file_content.encode('utf-8'))
    document = list(k.features())
    parse_placemarks(document)

    return basin_dict


# create polygon for basins
def parse_polygon(basin_dict, placemark):
    if isinstance(placemark.geometry, kml_geometry.Polygon):
        coordinates = [latlon2yx(x[0], x[1]) for x in placemark.geometry.exterior.coords]
        polygon = shapely_geometry.Polygon(shapely_geometry.LineString(coordinates))
        schema = list(list(placemark.extended_data.elements)[0].data)
        basin_name = [x['value'] for x in schema if x['name'] == "Basin_Name"][0]
        subbasin_name = [x['value'] for x in schema if x['name'] == "Basin_Subbasin_Name"][0]
        name = basin_name + ": " + subbasin_name
        basin_dict[name] = polygon


def create_mask(x, y):
    my_mask = np.ones((x, y))
    for i in range(x):
        for j in range(y):
            if not in_polygon((j, i)):
                my_mask[i][j] = np.nan

    h5f = h5py.File('my_mask.h5', 'w')
    h5f.create_dataset('mask', data=my_mask)
    h5f.close()


def main():
    if not os.path.isfile('basins.pickle') or not os.path.isfile('polygon.pickle'):
        basin_dict = create_basin_dict('input.kml')
        save_to_file('basins.pickle', basin_dict)
        save_to_file('polygon.pickle', basin_dict['SAN GABRIEL VALLEY: SAN GABRIEL VALLEY'])

    create_mask(324, 540)


if __name__ == '__main__':
    main()
