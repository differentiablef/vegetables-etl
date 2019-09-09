# ## imports ###################################################################

# local
from topics import words, begin, end

# standard lib
import requests, sys, os, time, json
from datetime import timezone, datetime

# parallel lib
from multiprocessing import Pool

# ### methods ##################################################################

def store_objects(path, obj, delimiter=','):
    # if the file doesn't exist, 
    if not os.path.isfile(path):
        # then don't include the delimiter
        delimiter = ''

    # append `obj` to file at `path` using `delimiter` to
    #  separate this batch from other elements of the file
    with open(path, 'a') as out:
        out.write(delimiter)
        json.dump(obj, out)
        pass


def get_objects(url, params, wait=2.0):
    # sleep for a bit before we send the request
    time.sleep(wait)

    # request resources from server
    res = requests.\
        get(url, params=params).\
        json()

    # return relevant portion of response and
    #   number of remaining results
    d = res.get('data')
    return (d, res.get('metadata').\
                   get('total_results') - len(d))

    
def collect_results(p):
    """ Collect all results from the time interval [`after`, `before`]
      by walking through the responses to GET requests sent to `url`;
      appending each collected batch to the file `path`.

      Note: this method assumes that "before" and "after" are valid 
          parameters for the endpoint, and accept UTC time-codes  """
    path, after, before, url, params = p

    # print something useful
    print(f'Storing Results in {path}')

    # initialize parameters 
    params.update(
        {'after': after,
         'before': before})

    # request initial batch
    data, size = get_objects(url, params)

    # store results
    store_objects(path, data)

    # get remaining results
    while size > 0:
        # set `after` to largest observed
        #  creation time from previous `data`
        after = data[-1].\
            get('created_utc')+1

        # update parameters
        params.\
            update({'after': after})

        # request and store next batch
        data, size = \
            get_objects(url, params)
        store_objects(path, data)
        pass


def main():
    # number of objects to request in a batch
    batch_size = 500
    
    # begin & end time as UTC ts.
    epoc = \
        int(begin.timestamp())

    apoc = \
        int(end.timestamp())

    # pushshift.io reddit api endpoints
    apis = {
        'https://api.pushshift.io/reddit/search/': {
            'comment':
            { 'q': None,
              'after': None,
              'before': None,
              'metadata': 'true',
              'size': batch_size,
              'sort': 'asc',
              'sort_type': 'created_utc' },
            
            'submission':
            {  'q': None,
               'after': None,
               'before': None,
               'metadata': 'true',
               'size': batch_size,
               'sort': 'asc',
               'sort_type': 'created_utc' }}}

    # create a pool of worker processes
    workers = Pool(4)

    # begin assigning work
    for url in apis:
        for endpoint in apis.get(url):
            print(f'Scheduling Work for {url+endpoint}')

            # build list of tasks
            args = []
            for word in words:
                params = apis[url][endpoint].copy()
                params['q'] = word
                
                args.append( 
                    (f'./imports/{endpoint}-{word}.json',
                     epoc, apoc,
                     url+endpoint, params))
            
            # assign tasks to the workers and wait
            workers.map( collect_results, args )

# ## script entry-point ########################################################

if __name__=="__main__":
    main()      # do primary task
    sys.exit(0) # exit cleanly
    
