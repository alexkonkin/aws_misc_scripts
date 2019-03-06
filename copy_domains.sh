#!/bin/bash

bucket=$1
domains=($(aws s3 ls s3://$bucket/models/ | awk '{print $2}'| sed 's/\///g'|xargs))
valid_files=(architecture.json encodings.json metrics.json model_weights.h5)

if [[ `echo $bucket|wc -m` == 1 ]];then
  echo "Please pass a bucket name to the script as the parameter"
  exit 1
fi

echo "Files that shold be present in each category are : "
echo -e "${valid_files[*]}\n"
echo "Domains that should be copied to the deploy folder after validation are : "
echo -e "${domains[*]}\n"

for domain in ${domains[*]};do
  echo "------------------------------"
  echo -e "Handling the Domain : $domain \n"
  model=$(aws s3 ls s3://$bucket/models/$domain/ --recursive | grep ma_resultset.json|sort|tail -n 1|awk '{print $4}'| awk -F/ '{print $3}')
  echo -e "The most recent model is: $model\n"
  categories=($(aws s3 cp s3://$bucket/models/$domain/$model/ma_resultset.json - | python -c "import sys, json; categories= json.load(sys.stdin)['models'];print (' '.join(categories));"))
  echo -e "Categories : ${categories[*]}\n"
  for category in ${categories[*]};do
    echo "Validating category : $category"
      category_files=($(aws s3 ls s3://$bucket/models/$domain/$model/$category/|awk '{ print $4}'|xargs))
      for valid_file in ${valid_files[*]};do
        if [[ ${category_files[@]} =~ $valid_file  ]];then
          echo "catetory file $valid_file is present"
          copy_cond=true
        else
          echo "catetory file $valid_file is absent"
          copy_cond=false
          break;
        fi
      done
  done

  if [[ $copy_cond == true ]]; then
    echo -e "\nSUCCESS:"
    echo "We can copy $domain with the model version $model to the deploy folder"
    copy_domain_cond=$(aws s3 cp --recursive s3://$bucket/models/$domain/$model/ s3://$bucket/deploy/$domain/ 1>/dev/null)
    if [[ $? == 0 ]];then
      echo "The domain $domain with the model $model has been successfully copied to the deploy folder" 
    fi
  else
    echo -e "\nERROR:"
    echo    "We can not copy $domain with the model $model to the deploy folder"
    echo    "Please have a look at the model : $model"
    echo -e "some mandatory files are missing in it\n"
  fi
  
done



