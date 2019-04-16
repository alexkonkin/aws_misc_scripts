import os
import boto3
import botocore
import argparse
import datetime
import sys
import json

parser = argparse.ArgumentParser(description='Copy recent version of domains to deploy folder')
parser.add_argument('-b','--bucket', help='name of the NaaS bucket', required=True)
parser.add_argument('-d','--delete', help='delete deploy folder before copy', required=True)
args = parser.parse_args()

valid_files = ['architecture.json', 'encodings.json', 'metrics.json', 'model_weights.h5']

s3 = boto3.resource('s3')

try:
  s3.meta.client.head_bucket(Bucket=args.bucket)

except botocore.exceptions.ClientError as e:
  error_code = e.response['Error']['Code']
  if error_code == '404':
    print ("The bucket %s does not exist" % args.bucket)
    exit (1)
else:
  print ("The bucket %s exists" % args.bucket)

client = boto3.client('s3')
prefix = 'models'
domains = []
result = client.list_objects(Bucket=args.bucket, Prefix=prefix + '/', Delimiter='/')
for o in result.get('CommonPrefixes'):
  domains.append((o.get('Prefix').strip(prefix).strip('/')))

print (domains)

#prefix1 = 'models/Fthwp_Demo'
#result1 = client.list_objects(Bucket=args.bucket, Prefix=prefix1 + '/', Delimiter='/')
#for o in result1.get('CommonPrefixes'):
#  print (o.get('Prefix'))

#for key in client.list_objects(Bucket=args.bucket, Prefix='models/Fthwp_Demo/', Delimiter='/')['Contents']:
#  print(key['Key'])

bucket = s3.Bucket(args.bucket)
recent_version = []
for domain in domains:
  config_file = []
  print ("Handling the domain %s " % domain)
  for s3_file in bucket.objects.all():
    if (s3_file.key.find('/'+domain+'/') != -1 and s3_file.key.find('ma_resultset.json') != -1 ):
      config_file.append(s3_file)

  print (config_file)
  print ('-------------')

  current_object=config_file[0]

  print(current_object)
  print ('--------------')
  for s3_file in config_file:
    if ( current_object.last_modified < s3_file.last_modified):
      current_object=s3_file

  print (current_object)
  recent_version.append(current_object)

for f in recent_version:
  current_category_files=[]
  domain_is_valid = True
  print(f.last_modified, f.key)
  content_object = s3.Object(args.bucket, f.key)
  file_content = content_object.get()['Body'].read().decode('utf-8')
  categories= json.loads(file_content)['models']
  print (categories)
  for category in categories:
    category_path = f.key.rpartition('ma_resultset.json')[0]
    for key in client.list_objects(Bucket=args.bucket, Prefix=category_path+category+'/', Delimiter='/')['Contents']:
      current_category_files.append(os.path.basename(key['Key']))
    
    print('current category files')
    print (current_category_files)
    
    for valid_file in valid_files:
      if valid_file not in current_category_files:
        domain_is_valid = False
        break

  if domain_is_valid == True:
    print ('Domain is valid '+ f.key)
  else:
    print ('Domain is not valid '+ f.key)

print ('---------')

