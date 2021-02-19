# GDAL Configuration

Titiler makes use of several great underlying libraries, including [GDAL][gdal]
and [Python bindings to GDAL][rasterio]. An effective deployment of titiler
generally requires tweaking GDAL configuration settings. This document provides
an overview of relevant settings. Full documentation from GDAL is available
[here][gdal_config_docs].

[gdal]: https://gdal.org/
[rasterio]: https://rasterio.readthedocs.io/
[gdal_config_docs]: https://gdal.org/user/configoptions.html

## Setting a config variable

GDAL configuration is modified using environment variables. Thus in order to
change a setting you'll need to set environment variables through your
deployment mechanism. For example, in order to test locally you'd set an
environment variable in bash:

```bash
export GDAL_HTTP_MULTIPLEX=YES
```

## Available configuration settings

#### `GDAL_HTTP_MULTIPLEX`

When set to `YES`, this attempts to download multiple range requests in
parallel, reusing the same TCP connection. Note this is only possible when the
server supports HTTP2, which many servers don't yet support. However there's no
downside to setting `YES` here.

#### `CPL_VSIL_CURL_ALLOWED_EXTENSIONS`

A list of file extensions that GDAL is allowed to open. For example if set to
`.tif`, then GDAL would only open files with a `.tif` extension. For example, it
would fail on JPEG2000 files with a `.jp2` extension, but also wouldn't open
GeoTIFFs exposed through an API endpoint that don't have a `.tif` suffix.

Note that you also need to include extensions of external overview files. For
example, the `landsat-pds` bucket on AWS S3 has external overviews in `.ovr`
files, so if you wished to read this data, you'd want

```bash
CPL_VSIL_CURL_ALLOWED_EXTENSIONS=.tif,.TIF,.ovr
```

#### `GDAL_INGESTED_BYTES_AT_OPEN`

Gives the number of initial bytes GDAL should read when opening a file and
inspecting its metadata.

Titiler works best with Cloud-Optimized GeoTIFFs (COGs) because they have a
tiled internal structure that supports efficient random reads. These files have
an initial metadata section that describes the location (byte range) within the
file of each internal tile. The more internal tiles the COG has, the more data
the header needs to contain.

GDAL needs to read the entire header before it can read any other portion of the
file. By default GDAL reads the first 16KB of the file, then if that doesn't
contain the entire metadata, it makes one more request for the rest of the
metadata.

In environments where latency is relatively high (at least compared to
bandwidth), such as AWS S3, it may be beneficial to increase this value
depending on the data you expect to read.

There isn't currently a way to get the number of header bytes using GDAL, but
alternative GeoTIFF readers such as [`aiocogeo`][aiocogeo] can. Using its cli
you can find the image's header size:

[aiocogeo]: https://github.com/geospatial-jeff/aiocogeo

```
> export AWS_REQUEST_PAYER="requester"
> aiocogeo info s3://usgs-landsat/collection02/level-2/standard/oli-tirs/2020/072/076/LC08_L2SR_072076_20201203_20201218_02_T2/LC08_L2SR_072076_20201203_20201218_02_T2_SR_B1.TIF

          PROFILE
            ...
            Header size:      32770
```

It's wise to inspect the header sizes of your data sources, and set
`GDAL_INGESTED_BYTES_AT_OPEN` appropriately. Beware, however, that the given
number of bytes will be read for every image, so you don't want to make the
value too large.

#### `GDAL_DISABLE_READDIR_ON_OPEN`

This is a very important setting to control the number of requests GDAL makes.

This setting has two options: `FALSE` and `EMPTY_DIR`. `FALSE` (the default)
causes GDAL to try to establish a list of all the available files in the
directory. `EMPTY_DIR` tells GDAL to imagine that the directory is empty except
for the requested file.

When reading datasets with necessary external sidecar files, it's imperative to
set `FALSE`. For example, the `landsat-pds` bucket on AWS S3 contains GeoTIFF
images where overviews are in external `.ovr` files. If set to `EMPTY_DIR`, GDAL
won't find the `.ovr` files.

However, in all other cases, it's much better to set `EMPTY_DIR` because this
prevents GDAL from making a `LIST` request.

This setting also has cost implications for reading data from requester-pays
buckets. When set to `FALSE`, GDAL makes a `LIST` request every time it opens a
file. Since `LIST` requests are much more expensive than `GET` requests, this
can bring unexpected costs.

#### `GDAL_HTTP_MERGE_CONSECUTIVE_RANGES`

When set to `YES`, this tells GDAL to merge adjacent range requests. Instead of
making two requests for byte ranges `1-5` and `6-10`, it would make a single
request for `1-10`. This should always be set to `YES`.

#### `GDAL_CACHEMAX`

#### `GDAL_DATA`

#### `PROJ_LIB`

#### `VSI_CACHE`

Setting this to `TRUE` enables GDAL to use an internal caching mechanism. It's
strongly recommended to set this to `TRUE`.

#### `VSI_CACHE_SIZE`

The size of the above VSI cache in bytes.