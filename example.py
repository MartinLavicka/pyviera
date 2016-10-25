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

    tv.ch_up()
    tv.ch_down()

else:
    print("No TVs could be found")
