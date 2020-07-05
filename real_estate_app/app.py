from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON_RETINA
from bokeh.tile_providers import get_provider
from bokeh.layouts import row
from bokeh.layouts import column

from bokeh.models.widgets.markups import Div
from bokeh.models import Select
from bokeh.models import TextInput

import requests

import math


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


class RealEstateApp:
    """An app used to display predictions of real estate data in Aarhus."""

    def __init__(self):
        """Initialize the app."""

        self.zipcodes = ['8000', '8200', '8210', '8230']
        self.selected_zipcode = None

        # Startup.
        self.layout = row(
            children=[],
            sizing_mode="fixed",
            width=1000,
        )
        self.refresh_plots()

    def refresh_plots(self):
        """Main function used to create all plots."""
        zipcode = Select(
            title="Postnummer:",
            value=self.selected_zipcode,
            options=self.zipcodes,
        )
        zipcode.on_change(
            'value',
            self.zipcode_handler
        )
        search = column(
            children=[zipcode]
        )
        if self.selected_zipcode is not None:
            address = Select(
                title="Vej:",
                value='value',
                options=self.get_roads(),
            )
            search.children.append(address)

        # Range bounds supplied in web mercator coordinates.
        range0 = merc(56.13, 10.18)
        range1 = merc(56.18, 10.26)
        aarhus_map = figure(
            x_range=(range0[0], range1[0]),
            y_range=(range0[1], range1[1]),
            x_axis_type="mercator",
            y_axis_type="mercator",
        )
        tile_provider = get_provider(CARTODBPOSITRON_RETINA)
        aarhus_map.add_tile(tile_provider)
        aarhus_map.toolbar.logo = None
        self.layout.children = [
            search,
            aarhus_map,
        ]

    def zipcode_handler(self, attr, old, new):
        self.selected_zipcode = new
        self.refresh_plots()

    def get_roads(self):
        return sorted(set(map(
            lambda response: response['vejstykke']['navn'],
            requests.get(
                'https://dawa.aws.dk/adgangsadresser',
                params={
                    'postnr': self.selected_zipcode,
                }
            ).json(),
        )))


planning_tool = RealEstateApp()
curdoc().add_root(planning_tool.layout)
curdoc().title = "Planning tool"
