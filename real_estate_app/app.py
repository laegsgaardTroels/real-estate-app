from real_estate_model import ModelPipeline

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

import pandas as pd

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

        self.model = ModelPipeline.load()

        self.zipcodes = ['8000', '8200', '8210', '8230']

        self.latitude_min = 56.13
        self.latitude_max = 56.18
        self.longitude_min = 10.18
        self.longitude_max = 10.26

        self.selected_zipcode = None
        self.selected_road = None
        self.selected_address = None
        self.selected_prediction = None

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
            self.zipcode_handler,
        )
        search = column(
            children=[zipcode]
        )
        if self.selected_zipcode is not None:
            road = Select(
                title="Vej:",
                value=self.selected_road,
                options=sorted(list(self.roads)),
            )
            road.on_change(
                'value',
                self.road_handler,
            )
            search.children.append(road)
            if self.selected_road is not None:
                address = Select(
                    title="Addresse:",
                    value=self.selected_address,
                    options=sorted(list(self.addresses)),
                )
                address.on_change(
                    'value',
                    self.address_handler,
                )
                search.children.append(address)
                if self.selected_prediction is not None:
                    formatted_price = (
                        f'{round(self.selected_prediction):,}'
                        .format(',', '.')
                    )
                    predicted_price = Div(
                        text=(
                            f"<p>Predicted price: {formatted_price} DKK</p>"
                        )
                    )
                    search.children.append(predicted_price)

        # Range bounds supplied in web mercator coordinates.
        range0 = merc(self.latitude_min, self.longitude_min)
        range1 = merc(self.latitude_max, self.longitude_max)
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
        self.selected_road = None
        self.selected_address = None
        self.selected_prediction = None
        self.selected_zipcode = new
        self.get_roads()
        self.refresh_plots()

    def road_handler(self, attr, old, new):
        self.selected_road = new
        self.selected_address = None
        self.selected_prediction = None
        self.get_addresses()
        self.refresh_plots()

    def address_handler(self, attr, old, new):
        self.selected_address = new
        self.selected_prediction = self.predict()
        print(self.selected_prediction)
        self.refresh_plots()

    def get_addresses(self):
        self.addresses = dict(map(
            lambda response: (response['adressebetegnelse'], response),
            requests.get(
                'https://dawa.aws.dk/adresser',
                params={
                    'navngivenvej_id': self.roads[self.selected_road]['id'],
                }
            ).json(),
        ))

    def get_roads(self):
        self.roads = dict(map(
            lambda response: (response['navn'], response),
            requests.get(
                'https://dawa.aws.dk/navngivneveje',
                params={
                    'postnr': self.selected_zipcode,
                }
            ).json(),
        ))

    def predict(self, addressid=None) -> float:
        if addressid is None:
            addressid = self.addresses[self.selected_address]['id']

        bbr_response = requests.get(
            'https://dawa.aws.dk/bbrlight/enheder',
            params={
                'adresseid': addressid,
            }
        )
        if bbr_response.status_code == 200:
            bbr = bbr_response.json()[0]
            return float(self.model.predict({
                'rooms': bbr['VAERELSE_ANT'],
                'size': bbr['BEBO_ARL'],
                'build_year': bbr['BEBO_ARL'],
                'latitude':  10,
                'longitude': 50,
            }))


planning_tool = RealEstateApp()
curdoc().add_root(planning_tool.layout)
curdoc().title = "Real Estate Model"
