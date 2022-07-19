# dscovrpy
Download a recent image of earth close to the current time of day. Images by epic on discovr https://epic.gsfc.nasa.gov/.

## Command Line Arguments
Argument | Description
--- | ---
`-o output_dir` | Path to the output directory
`-n pics_per_day` | Pick a day with at least `pics_per_day` pictures. Higher values lead to pictures, which tend to be closer to the current time of day. Lower values lead to pictures closer to the time of year. There is a maximum value of 24.
`-b background` | Path to the background image. The epic picture will be pasted onto the center of the background, resizing it, to be the same height. Dark, near black backgrounds work best.
`-c ` | Removes partially downloaded pictures from the output directory
## Examples
Image source: [https://epic.gsfc.nasa.gov/archive/natural/2018/07/19/png/epic_1b_20180719181319.png](https://epic.gsfc.nasa.gov/archive/natural/2018/07/19/png/epic_1b_20180719181319.png)
### Image with Background
``` bash
$ python ./dscovr.py -b example_background.jpg
epic_1b_20180719181319.png downloaded
``` 
![Epic with background](example_epic_background.png)

### Save to Output Directory
``` bash
$ python3 ./dscovr.py -o ~/.cache/dscovr
epic_1b_20180719181319.png downloaded
$ ls ~/.cache/dscovr
epic.png  image_info.epic
```
![Epic](example_epic.png)

## Conky

To use the conky lua script you need to set the PATH variable manually in the file. The script provides conky the function `epic_date`, which returns the date of the current picture in the local timezone. A lua datetime format can be set as an argument. Example:
```
${lua epic_date %d.%m.%y} # dd.mm.yyyy
${lua epic_date %X} # hh:MM:ss
```
