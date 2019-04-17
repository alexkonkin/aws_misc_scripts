#!/usr/bin/env python3.6

import os
import boto3
import botocore
import argparse
import datetime
import sys
import json

parser = argparse.ArgumentParser(description='Copy recent version of domains to deploy folder')
parser.add_argument('-b','--bucket', help='name of the NaaS bucket', required=True)
args = parser.parse_args()

valid_files = ['architecture.json', 'encodings.json', 'metrics.json', 'model_weights.h5']

s3 = boto3.resource('s3')

'''
Check if the bucket that is passed as a parameter exists in s3
'''
try:
  s3.meta.client.head_bucket(Bucket=args.bucket)

except botocore.exceptions.ClientError as e:
  error_code = e.response['Error']['Code']
  if error_code == '404':
    print ("The bucket %s does not exist" % args.bucket)
    exit (1)
else:
  print ("The bucket %s exists" % args.bucket)

'''
Clear the /deploy folder which might contain
previous versions of domains
'''
bucket = s3.Bucket(args.bucket)
bucket.objects.filter(Prefix="deploy/").delete()

'''
Get the list of domains that should be handled
'''
client = boto3.client('s3')
prefix = 'models'
domains = []
result = client.list_objects(Bucket=args.bucket, Prefix=prefix + '/', Delimiter='/')
for o in result.get('CommonPrefixes'):
  domains.append((o.get('Prefix').strip(prefix).strip('/')))

print ('Script will check and copy the domains : ')
print (domains)

'''
Get the most modern version of the model for each domain
'''
bucket = s3.Bucket(args.bucket)
recent_version = []
for domain in domains:
  config_file = []
  print ("Handling the domain %s " % domain)
  for s3_file in bucket.objects.all():
    if (s3_file.key.find('/'+domain+'/') != -1 and s3_file.key.find('ma_resultset.json') != -1 ):
      config_file.append(s3_file)

  current_object=config_file[0]

  for s3_file in config_file:
    if ( current_object.last_modified < s3_file.last_modified):
      current_object=s3_file

  recent_version.append(current_object)

'''
Validate most modern version of model (please see a set of files above)
and copy them if the model has all of them in place
'''
for f in recent_version:
  print ('--------------------------------------------------------')
  domain_is_valid = True

  content_object = s3.Object(args.bucket, f.key)
  file_content = content_object.get()['Body'].read().decode('utf-8')
  categories= json.loads(file_content)['models']

  for category in categories:
    current_category_files=[]
    category_path = f.key.rpartition('ma_resultset.json')[0]
    for key in client.list_objects(Bucket=args.bucket, Prefix=category_path+category+'/', Delimiter='/')['Contents']:
      current_category_files.append(os.path.basename(key['Key']))

    for valid_file in valid_files:
      if valid_file not in current_category_files:
        domain_is_valid = False
        break

  if domain_is_valid == True:
    print ('Domain is valid '+ os.path.basename(os.path.dirname(os.path.dirname(f.key))))
    objs = bucket.objects.filter(Prefix=os.path.dirname(f.key))
    for obj in objs:
      print ('copy from location : ' + obj.key)
      print ('to location : ' + 'deploy/'+ os.path.basename(os.path.dirname(os.path.dirname(f.key)))  +'/'+ os.path.relpath(obj.key, os.path.dirname(f.key)))
      s3.meta.client.copy({'Bucket': args.bucket, 'Key': obj.key}, args.bucket, 'deploy/'+ os.path.basename(os.path.dirname(os.path.dirname(f.key)))  +'/'+ os.path.relpath(obj.key, os.path.dirname(f.key)))
  else:
    print ('ERROR: domain is not valid '+ os.path.basename(os.path.dirname(os.path.dirname(f.key))))
