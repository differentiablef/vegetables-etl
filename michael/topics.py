
# need for time conversion
from datetime import datetime, timezone


# set of words we are interested in
words = \
    {'asparagus', 'broccoli', 'squash', 'spinach'}


# beginning and end of region of dates we care about

begin = datetime(2015, 1, 1).\
    replace(tzinfo=timezone.utc)

end = datetime.utcnow()


