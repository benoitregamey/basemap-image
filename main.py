from BasemapExtractor import BasemapExtractor

perimeter = (2737020, 5722885, 2742854, 5715473)
outdir = '/Users/benoitregamey/Desktop/Le_Vandrouilleur/Media/Book/test'
tiles_source = 'https://api.maptiler.com/maps/topo/256'
end_url = '@2x.png?key=OeICOfldMgEZFl7CAgF2'

basemap = BasemapExtractor(perimeter, 14, outdir, tiles_source, end_url)
basemap.download_tiles()
basemap.mosaic_tiles()