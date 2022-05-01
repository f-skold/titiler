
"""AWS Sentinel 2 readers."""

import logging

import json
import re
from collections import OrderedDict
from typing import Any, Dict, Sequence, Type, Union

import attr
from morecantile import TileMatrixSet
from rasterio.crs import CRS
from rasterio.features import bounds as featureBounds

from rio_tiler.constants import WEB_MERCATOR_TMS, WGS84_CRS
from rio_tiler.errors import InvalidBandName
from rio_tiler.io import COGReader, MultiBandReader
from rio_tiler_pds.sentinel.utils import s2_sceneid_parser
from rio_tiler_pds.utils import get_object

default_l1c_bands = (
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B09",
    "B11",
    "B12",
    "B8A",
)

actual_l1c_bands = (
    "B03",
    "B04",
    "B08",
)
@attr.s
class S2L2ACOGReaderFF(MultiBandReader):
    """Modded AWS Public Dataset Sentinel 2 L2A COGS reader.

    Args:
        input (str): Sentinel-2 sceneid.

    Attributes:
        minzoom (int): Dataset's Min Zoom level (default is 8).
        maxzoom (int): Dataset's Max Zoom level (default is 14).
        scene_params (dict): scene id parameters.
        bands (tuple): list of available bands (defined by the STAC item.json).
        stac_item (dict): sentinel 2 COG STAC item content.

    Examples:
        >>> with S2L2ACOGReader('S2A_29RKH_20200219_0_L2A') as scene:
                print(scene.bounds)

    """

    input: str = attr.ib()
    tms: TileMatrixSet = attr.ib(default=WEB_MERCATOR_TMS)

    reader: Type[COGReader] = attr.ib(default=COGReader)
    reader_options: Dict = attr.ib(factory=dict)

    minzoom: int = attr.ib(default=8)
    maxzoom: int = attr.ib(default=14)

    stac_item: Dict = attr.ib(init=False)

    _scheme: str = "s3"

    # "sentinel-cogs"
    hostname: str = attr.ib(default="sn-satellite")
    # prefix: str = attr.ib(default="sentinel-s2-{_levelLow}-cogs/{_utm}/{lat}/{sq}/{acquisitionYear}/{_month}/S{sensor}{satellite}_{_utm}{lat}{sq}_{acquisitionYear}{acquisitionMonth}{acquisitionDay}_{num}_{processingLevel}")
    prefix: str = attr.ib(default="s2_{acquisitionYear}_{acquisitionMonth}/{_utm}{lat}{sq},{acquisitionYear}-{acquisitionMonth}-{acquisitionDay},{num}")

    def __attrs_post_init__(self):
        """Fetch item.json and get bounds and bands."""
        # self.scene_params = s2_sceneid_parser(self.input)
        self.scene_params = self.input.scene_metadata

        #cog_sceneid = "S{sensor}{satellite}_{_utm}{lat}{sq}_{acquisitionYear}{acquisitionMonth}{acquisitionDay}_{num}_{processingLevel}".format(
        #    **self.scene_params
        #)
        prefix2 = self.prefix.format(**self.scene_params)
        # log1.info(f"Hostanme, path: {self.hostname} {prefix2}/tileInfo.json")
        self.bands = ""
        self.crs =  WGS84_CRS
        self.stac_item = None
        self.tileInfo = None
        try:
            self.tileInfo = json.loads(
                get_object(self.hostname, f"{prefix2}/tileInfo.json")
                # , request_pays=True
            )

            self.datageom = self.tileInfo["tileDataGeometry"]
            self.bounds = featureBounds(self.datageom)
            self.crs = CRS.from_user_input(self.datageom["crs"]["properties"]["name"])

            self.bands = actual_l1c_bands
        except Exception:
            log1 = logging.getLogger("uvicorn.error")
            log1.error(f"Failed to read from S3:  {self.hostname}, {prefix2}/tileInfo.json")


    def _get_band_url(self, band: str) -> str:
        """Validate band name and return band's url."""
        if "" == band:
            return "hej"
        band = band if len(band) == 3 else f"B0{band[-1]}"

        if band not in self.bands:
            raise InvalidBandName(f"{band} is not valid.\nValid bands: {self.bands}")

        prefix = self.prefix.format(**self.scene_params)
        return f"{self._scheme}://{self.hostname}/{prefix}/{band}.tif"


def S2COGReaderFF(sceneid: str, **kwargs: Any) -> S2L2ACOGReaderFF:
    """Modded Sentinel-2 COG readers."""
    log1 = logging.getLogger("uvicorn.error")
    # log1.info(f"Dump sceneid: {sceneid}")
    scene_params = sceneid.scene_metadata
    level = scene_params["processingLevel"]
    if level in ["L2A", "L1C"]:
        try:
            return S2L2ACOGReaderFF(sceneid, **kwargs)
        except Exception:
            return "Strange"
    else:
        log1.error(f"{level} is not supported, {sceneid}")
        raise Exception(f"{level} is not supported")
