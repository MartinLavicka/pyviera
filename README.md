# PyViera

PyViera allows you control your Panasonic VIERA TV using Python.

## Example

```python
from pyviera import Viera, COMMANDS

# List out all possible commands
print(COMMANDS.keys())
print()

# Look for any supported TVs
tvs = Viera.discover()

# Make sure we have at least one
if len(tvs) > 0:
    # Get the first TV that was found
    tv = tvs[0]

    # Send TV commands
    tv.mute()
    tv.vol_up()
    tv.num(5)

else:
    print("No TVs could be found")
```

## Compatibility
According to the description on the [app store](https://itunes.apple.com/us/app/panasonic-tv-remote-2/id590335696?mt=8), the following models are supported:

    Panasonic flat-panel TV, 2011/2012/2013/2014/2015 VIERA


## Contributors
This is a forked repository, based on [tomokas](https://github.com/tomokas/pyviera) work.
