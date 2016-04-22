# Large Images

## `red-19000x19000.png`

This is an all-red image 19000 by 19000 pixels (~300M pixels) which can be expressed as a PNG using a 1bit colormap in just 44kB.

```
iiif> file testimages/red-19000x19000.png 
testimages/red-19000x19000.png: PNG image data, 19000 x 19000, 1-bit colormap, non-interlaced
iiif> ls -l testimages/red-19000x19000.png 
-rw-r--r--+ 1 simeon  staff  44024 Sep  9 17:10 testimages/red-19000x19000.png
```

Expanding this to an 8bit-per-pixel RGB image without would create a 1GB image. This can be handled correctly by the PIL manipulator for the generation of static files (though it shows a warning). The region and size manipulations are done with the efficient pallete image, only at the quality stage is the image converted into an RGB image. To create a set of over 2000 tiles run:

```
iiif> rm -rf demo-static/red-19000x19000 demo-static/red-19000x19000.html; ./iiif_static.py --write-html demo-static -d demo-static -t 1024 testimages/red-19000x19000.png
```

and then with a server running with the repository directory as root, look at: <http://localhost:8000/demo-static/red-19000x19000.html>.

## Online large images

  * NASA Blue Marble <http://visibleearth.nasa.gov/view.php?id=73938>
