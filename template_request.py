import json
import psycopg2
import pandas as pd

# load credentials
creds = '/home/benoit.beranger/credentials_nifti2database_xnat-prod_ro.json'
with open(creds, 'r') as fid:
    cred_dic = json.load(fid)

# open DB connection
con = psycopg2.connect(
            database  =cred_dic['database'],
            user      =cred_dic['user'    ],
            password  =cred_dic['password'],
            host      =cred_dic['host'    ],
            port      =cred_dic['port'    ],
            # sslmode   ='disable',
            # gssencmode='disable',
        )
cur = con.cursor()

# perform SQL request
cur.execute(f"select distinct dict->'Resolution' as Resolution, count(*)  from xdat_search.nifti_json "
            f"where dict->>'PulseSequenceName'='tfl' and jsonb_typeof(dict->'InversionTime')='number'"
            f"group by dict->'Resolution' order by count desc;")
res = cur.fetchall()

df = pd.DataFrame(res)
print(df)
