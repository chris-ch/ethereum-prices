# ethereum-prices

## Pre-requisites

### AWS Configuration
Create an Access Key for your User in the AWS console (top left, "Security credentials") for the CLI Use Case.

Keep track of the Access Key and its related Secret key. From the command-line run `aws configure`.

Environment variables required for the project:

```shell
cat > .env <<EOT
TF_VAR_aws_stage=test
TF_VAR_aws_region=us-east-1
AWS_ACCESS_KEY_ID=xxxx
AWS_DEFAULT_REGION=us-east-1
AWS_SECRET_ACCESS_KEY=xxxx
DERIBIT_CLIENT_ID=xxxx
DERIBIT_CLIENT_SECRET=xxxx
SLACK_WEBHOOK_URL=xxxx
TF_VAR_slack_webhook_url=${SLACK_WEBHOOK_URL}
TF_VAR_s3_bucket_states=xxxx
EOT
```

Manually setting variables from `.env`:

```shell
export $(cat .env | grep -v '^#' | xargs)
```

Manually initialize OpenTofu:
```shell
export TF_VAR_aws_stage="test"
export TF_VAR_aws_region="us-east-1"
export TF_VAR_aws_account_id="$(aws sts get-caller-identity | jq -r '.Account')"
```

## Testing

`poetry run pytest`

## Scripts

`aws s3 ls s3://test-binance-prices-255120844515`

`poetry run aggregate-prices --bucket-name=test-binance-prices-255120844515 --instrument-code=ETHUSDT --count-years=6`

`poetry run deribit-account -i $DERIBIT_CLIENT_ID -s $DERIBIT_CLIENT_SECRET --currency ETH`
