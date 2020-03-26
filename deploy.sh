echo -e "3\nIndigoApp\nY\n1\nn\nn" | eb init -i
eb create indigo-app
aws codepipeline create-pipeline --cli-input-json file://pipeline.json --profile pa_iam