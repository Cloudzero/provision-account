# how to get set up

export AWS_PROFILE=cz-research.AdministratorAccess

aws sso login --profile cz-research.AdministratorAccess

export KOPS_STATE_STORE=s3://cz-kops-base

kops export kubecfg --admin

