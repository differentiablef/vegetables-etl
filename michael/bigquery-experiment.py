# ##############################################################################

import sys, json
from google.cloud import bigquery

# ##############################################################################

# bigquery data source 
source = \
    'fh-bigquery.reddit_comments'

# list of features we want to extract
features = \
    ['created_utc',
     'body',
     'author',
     'subreddit',
     'score',
     'id']

# set of words we are interested in
words = \
    {'asparagus', 'broccoli', 'squash', 'spinach'}

# conjunctive normal from 
#    of condition used to select feature vectors  
conditions = \
    [#[f"subreddit='AskReddit'"],
     [f"score IS NOT NULL"],
     [f"STRPOS(LOWER(body), '{word}') > 0"\
                          for word in words ]]

# ##############################################################################

def compile_query(conditions, year, month=1, rlimit=None):
    """ construct SQL SELECT statement which returns only 
          those tuples of `features` meeting the 
             the condition described by `conditions` """

    paren = "({})"
    
    # SQL fragment representing a feature vector
    rows = ", ".join(features)

    # assemble condition into SQL statement
    aconds = " AND ".join([paren.format(
                 " OR ".join(cases))\
                         for cases in conditions ])
    
    # construct SQL SELECT statement by keeping
    #   only the variables `month` and `year` free.
    select_fmt = \
        f"SELECT {rows}"+\
        f" FROM `{source}." +\
                "{year}_{month:02}`"+\
        f" WHERE {aconds}"
    
    if rlimit: 
        select_fmt += f" LIMIT {rlimit}"

    select_fmt = paren.format(select_fmt)
    
    # if month is provided and an integer, then ...
    if type(month) is int:
        if type(year) is int: # return single statement
            return select_fmt.\
                format(month=month, year=year)
        
        elif type(year) in {list,set}:
            return paren.format(\
                "\n UNION ALL \n".\
                    join([select_fmt.\
                          format(month=month, year=jj) for jj in year]))

    elif type(month) in {list, set}:
        # then, construct SQL fragment by combining expressions
        #      return resulting from assigning `month` a value appearing in list
        #        while keeping the variable `year` free. 
        select_fmt=paren.format(\
            "\n UNION ALL \n".\
                join([select_fmt.\
                      format(month=ii, year='{year}') for ii in month]))
        
        if type(year) is int:
            return select_fmt.\
                format(year=year)
        
        elif type(year) in {list, set}:
            return paren.format(\
                "\n UNION ALL \n".\
                    join([select_fmt.\
                          format(year=jj) for jj in year]))
        pass
    raise Exception("Should not get here")

# ##############################################################################

if __name__=="__main__":
    cfg = bigquery.QueryJobConfig()

    cfg.dry_run = False
    cfg.maximum_bytes_billed = 200*(10**9); # ~$2
    
    qstr = compile_query(conditions,
                         {2019},
                         {1,2,3,4,5})
    
    qstr = f"SELECT {', '.join(features)} FROM {qstr}"
    print('-'*70)
    print(qstr)
    print('-'*70)
    
    cl = bigquery.Client()
    jobq = cl.query(qstr, cfg,
                    location='US')

    print("Gigabytes Processed: {:10.03f}".format(
        jobq.total_bytes_processed/10**9))

    assert cfg.dry_run == False

    # Now that we're committed, we'll go ahead and save 
    output = []
    for ii, entry in enumerate(jobq):
        
        output.append(
            {f: entry[f] for f in features })

        if ii % 10000 == 0:
            with open('imports/data/out.json', 'a') as out:
                json.dump(output, out)            
            del output
            output = []

            print(f"{ii} ", end='', flush=True)
            pass
        pass
    with open('imports/data/out.json', 'a') as out:
        json.dump(output, out)
        pass

