import gzip
import re
import os
import numpy
from m2g.utils.cloud_utils import get_matching_s3_objects
from m2g.utils.cloud_utils import s3_client

RunTimes = {}
RunTimes['func']={}
RunTimes['dwi']={}

failcount = 0

bucket = 'ndmg-results'
path = 'runlogs'
localpath = '/Users/ross/Documents'

all_files = get_matching_s3_objects(bucket, path, suffix="gz")
client = s3_client(service="s3")


qq=0
for fi in all_files:
    client.download_file(bucket, fi, f"{localpath}/runlogs/{qq}.gz")
    print(f"Downloaded {qq}.gz")
    duration=None

    with gzip.open(f'{localpath}/runlogs/{qq}.gz', 'rt') as f:
        file_content = f.read()

        #find dataset, sub, and ses
        try:
            match = re.search("Downloading\s*\w*\-*\w*\/sub\-\d*\/ses\-\d*",file_content)
            source = match.group()
            source = source.split(' ')[1]
            dataset = source.split('/')[0]
            sub = source.split('sub-')[1].split('/')[0]
            ses = source.split('ses-')[1]
            good = True
        except:
            print('FAILURE to retrieve dataset/sub/ses')
            good = False
            pass
        

        #dMRI
        a = file_content.find('Total execution time: ')
        if a > -1 and good:
            dtype = 'dwi'
            dur = file_content[a+21:a+33]
            dhours = int(dur.split(':')[0])
            dminutes = int(dur.split(':')[1])
            dseconds = float(dur.split(':')[2])

            duration = ((((dhours*60)+dminutes)*60)+dseconds)

            print('dMRI')

        #fMRI
        b = file_content.find('System time of start: ')
        if b > -1 and good:
            dtype = 'func'
            c = file_content.find('System time of completion: ')
            
            if c > -1:
                start = file_content[b+38:b+46]
                end = file_content[c+38:c+46]

                #Convert start and end into numbers
                shours = int(start.split(':')[0])
                sminutes = int(start.split(':')[1])
                sseconds = int(start.split(':')[2])

                ehours = int(end.split(':')[0])
                eminutes = int(end.split(':')[1])
                eseconds = int(end.split(':')[2])

                duration = ((((ehours*60)+eminutes)*60)+eseconds) - ((((shours*60)+sminutes)*60)+sseconds)
                print('fMRI')
            else:
                print('fMRI')
                print("ERROR: Log denotes failure to complete")

        #failure
        d = file_content.find('m2g [-h]')
        if d > -1:
            duration = None


        if duration and duration < 800:
            print('Analysis less than 15 minutes')
            duration=None

        if not duration:
            print('FAILURE to calculate Duration')
            failcount=failcount+1      

        #Store values in giant array
        if dataset not in RunTimes[dtype].keys():
            if duration and good:
                RunTimes[dtype][dataset] = numpy.zeros(0)
                RunTimes[dtype][dataset] = numpy.append(RunTimes[dtype][dataset],[duration])
        else:
            if duration and good:
                RunTimes[dtype][dataset] = numpy.append(RunTimes[dtype][dataset],[duration])

    f.close()
    os.remove(f'{localpath}/runlogs/{qq}.gz')
    qq=qq+1


#Calculate average times
#numpy.sum(zz['a'])
#numpy.size(zz['a'])

print('oof')
