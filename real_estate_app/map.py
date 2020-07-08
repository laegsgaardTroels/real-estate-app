from real_estate_app import config

from bokeh.plotting import figure

from bokeh.tile_providers import CARTODBPOSITRON_RETINA
from bokeh.tile_providers import get_provider

from bokeh.models import ColumnDataSource

from bokeh.layouts import row

import pandas as pd

import math


class Map:
    """A map used to display the location of the real estate."""

    def __init__(
        self,
        latitude_min,
        latitude_max,
        longitude_min,
        longitude_max,
    ):
        self.latitude_min = latitude_min
        self.latitude_max = latitude_max
        self.longitude_min = longitude_min
        self.longitude_max = longitude_max

        self.address_coordinates = None

        self.tile_provider = get_provider(CARTODBPOSITRON_RETINA)

        self.address_source = ColumnDataSource()
        self.address_source.data = pd.DataFrame(
            columns=['x', 'y', 'adressebetegnelse', 'prediction']
        )

        # Startup.
        self.layout = row(
            children=[],
            width=config.WIDTH,
        )

    def refresh_plots(self):

        # Range bounds supplied in web mercator coordinates.
        self.x_range = (
            merc(self.latitude_min, self.longitude_min)[0],
            merc(self.latitude_max, self.longitude_max)[0],
        )
        self.y_range = (
            merc(self.latitude_min, self.longitude_min)[1],
            merc(self.latitude_max, self.longitude_max)[1],
        )
        self.aarhus_map = figure(
            x_range=self.x_range,
            y_range=self.y_range,
            x_axis_type="mercator",
            y_axis_type="mercator",
            tooltips=[
                ("Address", "@adressebetegnelse"),
                ("Prediction", "@prediction"),
            ],
        )
        self.aarhus_map.add_tile(self.tile_provider)
        self.aarhus_map.circle(
            x='x',
            y='y',
            size=5,
            fill_color="blue",
            fill_alpha=0.8,
            source=self.address_source,
        )
        self.aarhus_map.toolbar.logo = None
        self.layout.children = [self.aarhus_map]

        self.address_coordinates = None

    def set_address_source_data(
        self,
        address_response,
    ):
        rows = []
        for response in address_response:
            longitude, latitude = (
                response['adgangsadresse']['adgangspunkt']['koordinater']
            )
            new_row = dict(zip(('x', 'y'), merc(latitude, longitude)))
            new_row['adressebetegnelse'] = response['adressebetegnelse']
            new_row['prediction'] = round(response['prediction'] / 1e6, 1)
            rows.append(new_row)
        self.address_source.data = pd.DataFrame(rows)

    def set_bbox(
        self,
        longitude_min,
        latitude_min,
        longitude_max,
        latitude_max,
    ):
        self.longitude_min = longitude_min - 0.001
        self.latitude_min = latitude_min - 0.001
        self.longitude_max = longitude_max + 0.001
        self.latitude_max = latitude_max + 0.001


def merc(lat, lon):
    r_major = 6378137.000
    x = r_major * math.radians(lon)
    scale = x/lon
    y = (
        180.0 / math.pi * math.log(
            math.tan(
                math.pi / 4.0 + lat * (math.pi / 180.0) / 2.0
            )
        ) * scale
    )
    return (x, y)
