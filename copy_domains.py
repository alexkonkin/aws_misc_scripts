import boto3
import botocore
import argparse

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




#print (naas_bucket)

#response = s3.list_buckets()

#buckets = [bucket['Name'] for bucket in response['Buckets']]

#print("Bucket List: %s" % buckets)


