# basemap-image
#### Get basemap as a single tiff file for any AOI and zoom level with the best quality possible !
You need an API Key from Maptiler in order to use this app. Create an account to get your API. It works only for tiles from Maptiler XYZ services with high DPI tiles (512x512 pixels instead of 256). It should be easily adapted for other XYZ tiles sources.
## Installation (mac)
- Clone the repo anywhere you like. 
- Unzip it. 
- Open the terminal
- Go to the root of the app directory (where the file BasemapExtractor.py is)
```sh
cd path/to/root/directory
```
## Usage
##### Example
```sh
./env/bin/python3.9 BasemapExtractor.py perimeter=2737020,5722885,2742854,5715473 zoomlevel=14 outdir=path-to-directory-where-to-save-the-image tiles_url=https://api.maptiler.com/maps/topo/256 key=your-personal-api-key-from-maptiler
```
Run the app with the given python virtual environment (./env/bin/python3.9). It includes all the necessary dependencies !

##### Options
```sh
perimeter=west,north,east,south   # Give the 4 coordinates of the AOI you want in EPSG:3857 (web-mercator, google maps)
```
```sh
zoomlevel=14   # Give the zoom level as an integer between 0 and 20
```
```sh
outdir=/path-to-directory   # Path to directory where to save temp files and final image output. Must exists !
```
```sh
tiles_url=https://api.maptiler.com/maps/{layer-name}/256   # URL of Maptiler XYZ service. Layer name must be given
```
```sh
key=your-personal-api-key-from-Maptiler
```
##### Execution
When you run the app, it tells you how many tiles are needed to be downloaded according to the given AOI and zoom level. You can abort the program if it's too much !