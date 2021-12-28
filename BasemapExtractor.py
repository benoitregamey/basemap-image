import requests
from PIL import Image
import os
import math
from pyproj import Transformer
import os
import osgeo_utils.gdal_merge
import sys

class BasemapExtractor:


    def __init__(self, perimeter, zoom_level, outdir, tiles_url, tiles_url_end='.png', highdpi=True, mosaic=True):
        """Set the perimter you want to extract in form of rectangle by giving a tuple with 4 coordinates
        in epsg_3857 (west, north, east, south). Set the zoom level you want. Set the directory where to save the image.
        Give the URL of the tiles source (WMTS, XYZ), the part before the zoom level. Give the URL end (@2x, format, key)
        Set mosaic to false if you don't want to mosaic the tiles together, default is True 
        """
        transformer = Transformer.from_crs(3857, 4326)

        self.perimeter = (
            transformer.transform(perimeter[0], perimeter[1])[1],
            transformer.transform(perimeter[0], perimeter[1])[0],
            transformer.transform(perimeter[2], perimeter[3])[1],
            transformer.transform(perimeter[2], perimeter[3])[0]
        )

        self.zoom_level = zoom_level
        self.outdir = outdir
        self.tiles_url = tiles_url
        self.tiles_url_end = tiles_url_end
        self.highdpi = highdpi
        self.mosaic = mosaic


    def get_tiles_id(self):
        """Get the 4 ids of border tiles. Return a tuple with border id (left, up, right, bottom)"""

        n = 2.0 ** self.zoom_level
        tile_left_id = int((self.perimeter[0] + 180.0) / 360.0 * n)
        tile_right_id = int((self.perimeter[2] + 180.0) / 360.0 * n)

        lat_rad = math.radians(self.perimeter[1])
        tile_up_id = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        lat_rad = math.radians(self.perimeter[3])
        tile_bottom_id = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)

        return (tile_left_id, tile_up_id, tile_right_id, tile_bottom_id)


    def get_tiles_number(self):
        """Return the number of tiles needed to cover the perimeter."""
        
        # /!\ the tiles id goes from top to bottom in the Y axis
        # That's why it's LowerLeft - UpperRight for the Y axis
        tiles_number = (self.get_tiles_id()[2] - self.get_tiles_id()[0] + 1) * (self.get_tiles_id()[3] - self.get_tiles_id()[1] + 1)
        print(f"\nNumber of tiles covering the perimeter : {tiles_number}\n")
        return tiles_number


    def tileid_2_coodrinates(self, tileid_x, tileid_y):
        """Take 2 arguments : tile id in X and Y. Return the coordinates in epsg:3857 of corner for worldfile"""
        n = 2.0 ** self.zoom_level
        lon_deg = tileid_x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * tileid_y / n)))
        lat_deg = math.degrees(lat_rad)
        transformer = Transformer.from_crs(4326, 3857)
        return transformer.transform(lat_deg, lon_deg)


    def download_tiles(self):
        """Download necessary tiles to cover the perimeter. Transform them into RGB JPEG 95% compression.
        Write the World File for each tile"""

        # Ask the user if he wants to continue, knowing the number of tiles to download
        tiles_total = self.get_tiles_number()
        if input("Press Enter to continue or anything else to stop : ") != "":
            return

        count = 0

        for x_coord in range(self.get_tiles_id()[0], self.get_tiles_id()[2]+1):
            for y_coord in range(self.get_tiles_id()[1], self.get_tiles_id()[3]+1):

                # Download the tiles from the WMTS API ENDPOINT
                with open(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.png', "wb") as file:
                    response = requests.get(self.tiles_url + '/' + str(self.zoom_level) + '/' + str(x_coord) + '/' + str(y_coord) + self.tiles_url_end)
                    file.write(response.content)
                    
                print(f"Downloaded Tile : {x_coord}_{y_coord}") 

                # Transform the file into RGB Image
                img = Image.open(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.png')
                imgRGB = img.convert('RGB')
                imgRGB.save(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.jpg', format='JPEG', subsampling=0, quality=95)
                os.remove(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.png')

                print(f"Converted to RGB Tile : {x_coord}_{y_coord}")

                # Write the World File
                if self.highdpi:
                    resolution = round(78271.515/(2**self.zoom_level), 4)
                else:
                    resolution = round(78271.515/(2**self.zoom_level)*2, 4)
                pixel_x = self.tileid_2_coodrinates(x_coord, y_coord)[0] + (resolution/2)
                pixel_y = self.tileid_2_coodrinates(x_coord, y_coord)[1] - (resolution/2)

                with open(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.jgw', 'w') as jgw:           
                    jgw.write(str(resolution) + '\n')
                    jgw.write('0\n')
                    jgw.write('0\n')
                    jgw.write('-' + str(resolution) + '\n')
                    jgw.write(str(pixel_x) + '\n')
                    jgw.write(str(pixel_y) + '\n')
            
                print(f"Created World File for the Tile : {x_coord}_{y_coord}")
                count += 1
                print(f"{round((count/tiles_total)*100, 2)} %\n")
     

    def mosaic_tiles(self):
        """Mosaic the tiles together. Uses the GDAL library. Must be installed sperately"""
        
        # First create a mosaic for each row of tiles 
        for x_coord in range(self.get_tiles_id()[0], self.get_tiles_id()[2]+1):
            optfile = open(self.outdir + '/optfile.txt', 'w')
            
            for y_coord in range(self.get_tiles_id()[1], self.get_tiles_id()[3]+1):
                optfile.write(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.jpg' + ' ')

            optfile.close()
                
            osgeo_utils.gdal_merge.main(['gdal_merge.py', '-o', self.outdir + '/' + str(x_coord) + '.tif', '-co', 'TFW=YES', '-co', 'TILED=YES', '-co', 'COMPRESS=LZW', '-co', 'PREDICTOR=2', '--optfile', self.outdir + '/optfile.txt'])

        # Then mosaic the row mosaics together in a single file
        with open(self.outdir + '/optfile.txt', 'w') as optfile:
            
            for x_coord in range(self.get_tiles_id()[0], self.get_tiles_id()[2]+1):
                optfile.write(self.outdir + '/' + str(x_coord) + '.tif' + ' ')
            
        osgeo_utils.gdal_merge.main(['gdal_merge.py', '-o', self.outdir + '/Mosaic.tif', '-co', 'TFW=YES', '-co', 'TILED=YES', '-co', 'COMPRESS=LZW', '-co', 'PREDICTOR=2', '--optfile', self.outdir + '/optfile.txt'])
        os.remove(self.outdir + '/optfile.txt')

        for x_coord in range(self.get_tiles_id()[0], self.get_tiles_id()[2]+1):
            os.remove(self.outdir + '/' + str(x_coord) + '.tif')
            os.remove(self.outdir + '/' + str(x_coord) + '.tfw')

        for x_coord in range(self.get_tiles_id()[0], self.get_tiles_id()[2]+1):
            for y_coord in range(self.get_tiles_id()[1], self.get_tiles_id()[3]+1):
                os.remove(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.jpg')
                os.remove(self.outdir + '/' + str(x_coord) + '_' + str(y_coord) + '.jgw')


def main(*args):

    for arg in args:

        if arg.split("=")[0] == "perimeter":
            boundingbox = arg.split("=")[1]
            perimeter = tuple(map(int, boundingbox.split(',')))

        elif arg.split("=")[0] == "outdir":
            outdir = arg.split("=")[1]
        
        elif arg.split("=")[0] == "tiles_url":
            tiles_url = arg.split("=")[1]

        elif arg.split("=")[0] == "key":
            tiles_url_end = '@2x.png?key=' + arg.split("=")[1]

        elif arg.split("=")[0] == "zoom_level":
            zoom_level = int(arg.split("=")[1])

    basemap = BasemapExtractor(perimeter=perimeter, zoom_level=zoom_level, outdir=outdir, tiles_url=tiles_url, tiles_url_end=tiles_url_end)
    basemap.download_tiles()
    basemap.mosaic_tiles()

if __name__ == "__main__":
    main(*sys.argv[1:])
        